const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("OsoolRegistry", function () {
    let OsoolRegistry;
    let registry;
    let owner;
    let seller;
    let buyer;

    beforeEach(async function () {
        [owner, seller, buyer] = await ethers.getSigners();

        OsoolRegistry = await ethers.getContractFactory("OsoolRegistry");
        registry = await OsoolRegistry.deploy();
        await registry.deployed();
    });

    describe("Deployment", function () {
        it("Should set the right owner", async function () {
            expect(await registry.owner()).to.equal(owner.address);
        });

        it("Should start with nextId = 1", async function () {
            const nextId = await registry.nextId();
            expect(nextId.toString()).to.equal("1");
        });

        it("Should start with totalListings = 0", async function () {
            const total = await registry.totalListings();
            expect(total.toString()).to.equal("0");
        });
    });

    describe("Property Listing", function () {
        const docHash = "QmTestHash123456789";
        const priceEGP = 5000000; // 5 Million EGP

        it("Should allow anyone to list a property", async function () {
            await registry.connect(seller).listProperty(docHash, priceEGP);

            const property = await registry.getProperty(1);
            expect(property.id.toString()).to.equal("1");
            expect(property.legalDocumentHash).to.equal(docHash);
            expect(property.priceEGP.toString()).to.equal(priceEGP.toString());
            expect(property.owner).to.equal(seller.address);
            expect(property.status).to.equal(0); // AVAILABLE
        });

        it("Should emit PropertyListed event", async function () {
            const tx = await registry.connect(seller).listProperty(docHash, priceEGP);
            const receipt = await tx.wait();

            // Check event was emitted
            const event = receipt.events.find(e => e.event === 'PropertyListed');
            expect(event).to.not.be.undefined;
            expect(event.args.id.toString()).to.equal("1");
            expect(event.args.owner).to.equal(seller.address);
        });

        it("Should increment nextId after listing", async function () {
            await registry.connect(seller).listProperty(docHash, priceEGP);
            const nextId = await registry.nextId();
            expect(nextId.toString()).to.equal("2");
        });

        it("Should reject empty document hash", async function () {
            try {
                await registry.connect(seller).listProperty("", priceEGP);
                expect.fail("Should have reverted");
            } catch (error) {
                expect(error.message).to.include("Document hash required");
            }
        });

        it("Should reject zero price", async function () {
            try {
                await registry.connect(seller).listProperty(docHash, 0);
                expect.fail("Should have reverted");
            } catch (error) {
                expect(error.message).to.include("Price must be positive");
            }
        });
    });

    describe("Property Reservation (Admin Only)", function () {
        const docHash = "QmTestHash123456789";
        const priceEGP = 5000000;

        beforeEach(async function () {
            await registry.connect(seller).listProperty(docHash, priceEGP);
        });

        it("Should allow owner to mark property as reserved", async function () {
            await registry.connect(owner).markReserved(1, buyer.address);

            const property = await registry.getProperty(1);
            expect(property.status).to.equal(1); // RESERVED
            expect(property.reservedBy).to.equal(buyer.address);
        });

        it("Should emit PropertyStatusChanged event", async function () {
            const tx = await registry.connect(owner).markReserved(1, buyer.address);
            const receipt = await tx.wait();

            const event = receipt.events.find(e => e.event === 'PropertyStatusChanged');
            expect(event).to.not.be.undefined;
            expect(event.args.status).to.equal(1); // RESERVED
        });

        it("Should reject non-owner from marking reserved", async function () {
            try {
                await registry.connect(seller).markReserved(1, buyer.address);
                expect.fail("Should have reverted");
            } catch (error) {
                expect(error.message).to.include("caller is not the owner");
            }
        });

        it("Should reject reserving non-existent property", async function () {
            try {
                await registry.connect(owner).markReserved(999, buyer.address);
                expect.fail("Should have reverted");
            } catch (error) {
                expect(error.message).to.include("Property does not exist");
            }
        });

        it("Should reject reserving already reserved property", async function () {
            await registry.connect(owner).markReserved(1, buyer.address);

            try {
                await registry.connect(owner).markReserved(1, buyer.address);
                expect.fail("Should have reverted");
            } catch (error) {
                expect(error.message).to.include("Not available");
            }
        });

        it("Should reject owner reserving own property", async function () {
            try {
                await registry.connect(owner).markReserved(1, seller.address);
                expect.fail("Should have reverted");
            } catch (error) {
                expect(error.message).to.include("Owner cannot reserve own property");
            }
        });
    });

    describe("Property Sale Finalization (Admin Only)", function () {
        const docHash = "QmTestHash123456789";
        const priceEGP = 5000000;

        beforeEach(async function () {
            await registry.connect(seller).listProperty(docHash, priceEGP);
            await registry.connect(owner).markReserved(1, buyer.address);
        });

        it("Should allow owner to finalize sale", async function () {
            await registry.connect(owner).markSold(1);

            const property = await registry.getProperty(1);
            expect(property.status).to.equal(2); // SOLD
            expect(property.owner).to.equal(buyer.address);
        });

        it("Should emit PropertySold event", async function () {
            const tx = await registry.connect(owner).markSold(1);
            const receipt = await tx.wait();

            const event = receipt.events.find(e => e.event === 'PropertySold');
            expect(event).to.not.be.undefined;
            expect(event.args.previousOwner).to.equal(seller.address);
            expect(event.args.newOwner).to.equal(buyer.address);
        });

        it("Should reject selling non-reserved property", async function () {
            await registry.connect(seller).listProperty(docHash, priceEGP);

            try {
                await registry.connect(owner).markSold(2);
                expect.fail("Should have reverted");
            } catch (error) {
                expect(error.message).to.include("Must be reserved first");
            }
        });
    });

    describe("Reservation Cancellation (Admin Only)", function () {
        const docHash = "QmTestHash123456789";
        const priceEGP = 5000000;

        beforeEach(async function () {
            await registry.connect(seller).listProperty(docHash, priceEGP);
            await registry.connect(owner).markReserved(1, buyer.address);
        });

        it("Should allow owner to cancel reservation", async function () {
            await registry.connect(owner).cancelReservation(1);

            const property = await registry.getProperty(1);
            expect(property.status).to.equal(0); // AVAILABLE
            expect(property.reservedBy).to.equal(ethers.constants.AddressZero);
        });

        it("Should reject cancelling non-reserved property", async function () {
            await registry.connect(seller).listProperty(docHash, priceEGP);

            try {
                await registry.connect(owner).cancelReservation(2);
                expect.fail("Should have reverted");
            } catch (error) {
                expect(error.message).to.include("Not reserved");
            }
        });
    });

    describe("View Functions", function () {
        const docHash = "QmTestHash123456789";
        const priceEGP = 5000000;

        beforeEach(async function () {
            await registry.connect(seller).listProperty(docHash, priceEGP);
        });

        it("Should return correct availability status", async function () {
            expect(await registry.isAvailable(1)).to.be.true;

            await registry.connect(owner).markReserved(1, buyer.address);
            expect(await registry.isAvailable(1)).to.be.false;
        });

        it("Should return owner listings", async function () {
            const listings = await registry.getOwnerListings(seller.address);
            expect(listings.length).to.equal(1);
            expect(listings[0].toString()).to.equal("1");
        });

        it("Should verify document hash correctly", async function () {
            expect(await registry.verifyDocument(1, docHash)).to.be.true;
            expect(await registry.verifyDocument(1, "WrongHash")).to.be.false;
        });
    });
});
