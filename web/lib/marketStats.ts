'use client';

/**
 * Market Statistics Computation Engine
 * Computes all 30+ KPIs client-side from the embedded property data.
 * This ensures the page works without a running backend.
 */

export interface MeterStats {
    min_meter: number;
    avg_meter: number;
    max_meter: number;
    count: number;
}

export interface RoomStats {
    count: number;
    avg_price: number;
    min_price: number;
    max_price: number;
    avg_size_sqm: number;
    avg_meter: number;
}

export interface BestDeal {
    property_id: string;
    title: string;
    price: number;
    price_per_sqm: number;
    developer: string;
    compound: string;
}

export interface DevLocEntry {
    developer: string;
    location: string;
    avg_meter: number;
    count: number;
}

export interface CompoundEntry {
    compound: string;
    developer: string;
    location: string;
    count: number;
    avg_meter: number;
}

export interface SizeBracket {
    count: number;
    avg_price: number;
    avg_meter: number;
    avg_size: number;
}

export interface PaymentStats {
    avg_down_payment: number;
    avg_installment_years: number;
    avg_monthly_installment: number;
    min_down_payment: number;
    max_down_payment: number;
    properties_with_plans: number;
}

export interface PriceBracket {
    count: number;
    avg_meter: number;
}

export interface DetailedStats {
    meter_price_by_area: Record<string, MeterStats>;
    meter_price_by_developer: Record<string, MeterStats>;
    meter_price_by_type: Record<string, MeterStats>;
    room_statistics: Record<string, RoomStats>;
    developer_by_location: Record<string, DevLocEntry>;
    best_price_per_area: Record<string, BestDeal>;
    best_price_per_developer: Record<string, BestDeal>;
    best_price_per_type: Record<string, BestDeal>;
    finishing_statistics: Record<string, MeterStats>;
    size_bracket_statistics: Record<string, SizeBracket>;
    payment_statistics: PaymentStats;
    price_bracket_distribution: Record<string, PriceBracket>;
    top_compounds: CompoundEntry[];
    summary: {
        total_properties: number;
        avg_price: number;
        avg_meter: number;
        min_meter: number;
        max_meter: number;
        areas_count: number;
        developers_count: number;
        types_count: number;
    };
}

interface RawProperty {
    id: string;
    title: string;
    type: string;
    location: string;
    compound: string;
    developer: string;
    area: string;
    size: string;
    sqm: number;
    bua: number;
    bedrooms: number;
    bathrooms: number;
    price: number;
    pricePerSqm: number;
    deliveryDate: string;
    paymentPlan: {
        downPayment: number;
        installmentYears: number;
        monthlyInstallment: number;
    };
    image: string;
    nawyUrl: string;
    saleType: string;
    description: string;
}

function groupBy<T>(arr: T[], keyFn: (item: T) => string): Record<string, T[]> {
    const map: Record<string, T[]> = {};
    for (const item of arr) {
        const key = keyFn(item);
        if (!key || key === 'nan' || key === 'undefined' || key === 'null') continue;
        if (!map[key]) map[key] = [];
        map[key].push(item);
    }
    return map;
}

function computeMeterStats(properties: RawProperty[]): MeterStats {
    const valid = properties.filter(p => p.pricePerSqm > 0);
    if (valid.length === 0) return { min_meter: 0, avg_meter: 0, max_meter: 0, count: properties.length };
    const meters = valid.map(p => p.pricePerSqm);
    return {
        min_meter: Math.min(...meters),
        avg_meter: meters.reduce((a, b) => a + b, 0) / meters.length,
        max_meter: Math.max(...meters),
        count: properties.length,
    };
}

function findBestDeal(properties: RawProperty[]): BestDeal | null {
    const valid = properties.filter(p => p.pricePerSqm > 0);
    if (valid.length === 0) return null;
    const best = valid.reduce((a, b) => a.pricePerSqm < b.pricePerSqm ? a : b);
    return {
        property_id: best.id,
        title: best.title,
        price: best.price,
        price_per_sqm: best.pricePerSqm,
        developer: best.developer,
        compound: best.compound,
    };
}

function getSizeBracketLabel(sqm: number): string {
    if (sqm <= 80) return 'Under 80 m²';
    if (sqm <= 120) return '80–120 m²';
    if (sqm <= 180) return '120–180 m²';
    if (sqm <= 250) return '180–250 m²';
    if (sqm <= 400) return '250–400 m²';
    return 'Over 400 m²';
}

function getPriceBracketLabel(price: number): string {
    if (price <= 2_000_000) return 'Under 2M EGP';
    if (price <= 5_000_000) return '2M – 5M EGP';
    if (price <= 10_000_000) return '5M – 10M EGP';
    if (price <= 20_000_000) return '10M – 20M EGP';
    if (price <= 50_000_000) return '20M – 50M EGP';
    return 'Over 50M EGP';
}

export function computeDetailedStats(properties: RawProperty[]): DetailedStats {
    const valid = properties.filter(p => p.price > 0);

    // Group by area
    const byArea = groupBy(valid, p => p.location || p.area);
    const meter_price_by_area: Record<string, MeterStats> = {};
    const best_price_per_area: Record<string, BestDeal> = {};
    for (const [area, props] of Object.entries(byArea)) {
        meter_price_by_area[area] = computeMeterStats(props);
        const deal = findBestDeal(props);
        if (deal) best_price_per_area[area] = deal;
    }

    // Group by developer
    const byDev = groupBy(valid, p => p.developer);
    const meter_price_by_developer: Record<string, MeterStats> = {};
    const best_price_per_developer: Record<string, BestDeal> = {};
    for (const [dev, props] of Object.entries(byDev)) {
        meter_price_by_developer[dev] = computeMeterStats(props);
        const deal = findBestDeal(props);
        if (deal) best_price_per_developer[dev] = deal;
    }

    // Group by type
    const byType = groupBy(valid, p => p.type);
    const meter_price_by_type: Record<string, MeterStats> = {};
    const best_price_per_type: Record<string, BestDeal> = {};
    for (const [type, props] of Object.entries(byType)) {
        meter_price_by_type[type] = computeMeterStats(props);
        const deal = findBestDeal(props);
        if (deal) best_price_per_type[type] = deal;
    }

    // Room statistics (by bedrooms)
    const byBedrooms = groupBy(valid, p => String(p.bedrooms ?? 0));
    const room_statistics: Record<string, RoomStats> = {};
    for (const [beds, props] of Object.entries(byBedrooms)) {
        const prices = props.map(p => p.price);
        const sizes = props.filter(p => p.bua > 0).map(p => p.bua);
        const meters = props.filter(p => p.pricePerSqm > 0).map(p => p.pricePerSqm);
        room_statistics[beds] = {
            count: props.length,
            avg_price: prices.reduce((a, b) => a + b, 0) / prices.length,
            min_price: Math.min(...prices),
            max_price: Math.max(...prices),
            avg_size_sqm: sizes.length > 0 ? sizes.reduce((a, b) => a + b, 0) / sizes.length : 0,
            avg_meter: meters.length > 0 ? meters.reduce((a, b) => a + b, 0) / meters.length : 0,
        };
    }

    // Developer by location cross-analysis
    const developer_by_location: Record<string, DevLocEntry> = {};
    for (const prop of valid) {
        const loc = prop.location || prop.area;
        const dev = prop.developer;
        if (!loc || loc === 'nan' || !dev || dev === 'nan') continue;
        const key = `${dev}__${loc}`;
        if (!developer_by_location[key]) {
            developer_by_location[key] = { developer: dev, location: loc, avg_meter: 0, count: 0 };
        }
        developer_by_location[key].count++;
        if (prop.pricePerSqm > 0) {
            developer_by_location[key].avg_meter += prop.pricePerSqm;
        }
    }
    for (const entry of Object.values(developer_by_location)) {
        if (entry.count > 0) entry.avg_meter = entry.avg_meter / entry.count;
    }

    // Top compounds
    const byCompound = groupBy(valid, p => p.compound);
    const top_compounds: CompoundEntry[] = Object.entries(byCompound)
        .map(([compound, props]) => {
            const meters = props.filter(p => p.pricePerSqm > 0).map(p => p.pricePerSqm);
            return {
                compound,
                developer: props[0]?.developer || '',
                location: props[0]?.location || props[0]?.area || '',
                count: props.length,
                avg_meter: meters.length > 0 ? meters.reduce((a, b) => a + b, 0) / meters.length : 0,
            };
        })
        .sort((a, b) => b.count - a.count)
        .slice(0, 15);

    // Size bracket statistics
    const size_bracket_statistics: Record<string, SizeBracket> = {};
    const sizeGroups = groupBy(valid.filter(p => p.bua > 0), p => getSizeBracketLabel(p.bua));
    for (const [label, props] of Object.entries(sizeGroups)) {
        const prices = props.map(p => p.price);
        const meters = props.filter(p => p.pricePerSqm > 0).map(p => p.pricePerSqm);
        const sizes = props.map(p => p.bua);
        size_bracket_statistics[label] = {
            count: props.length,
            avg_price: prices.reduce((a, b) => a + b, 0) / prices.length,
            avg_meter: meters.length > 0 ? meters.reduce((a, b) => a + b, 0) / meters.length : 0,
            avg_size: sizes.reduce((a, b) => a + b, 0) / sizes.length,
        };
    }

    // Payment statistics
    const withPlans = valid.filter(p =>
        p.paymentPlan &&
        typeof p.paymentPlan === 'object' &&
        p.paymentPlan.downPayment > 0
    );
    const downPayments = withPlans.map(p => p.paymentPlan.downPayment);
    const installYears = withPlans.map(p => p.paymentPlan.installmentYears);
    const monthlyInst = withPlans.filter(p => p.paymentPlan.monthlyInstallment > 0).map(p => p.paymentPlan.monthlyInstallment);
    const payment_statistics: PaymentStats = {
        avg_down_payment: downPayments.length > 0
            ? Math.round(downPayments.reduce((a, b) => a + b, 0) / downPayments.length * 10) / 10
            : 0,
        avg_installment_years: installYears.length > 0
            ? Math.round(installYears.reduce((a, b) => a + b, 0) / installYears.length * 10) / 10
            : 0,
        avg_monthly_installment: monthlyInst.length > 0
            ? Math.round(monthlyInst.reduce((a, b) => a + b, 0) / monthlyInst.length)
            : 0,
        min_down_payment: downPayments.length > 0 ? Math.min(...downPayments) : 0,
        max_down_payment: downPayments.length > 0 ? Math.max(...downPayments) : 0,
        properties_with_plans: withPlans.length,
    };

    // Price bracket distribution
    const price_bracket_distribution: Record<string, PriceBracket> = {};
    const priceGroups = groupBy(valid, p => getPriceBracketLabel(p.price));
    for (const [label, props] of Object.entries(priceGroups)) {
        const meters = props.filter(p => p.pricePerSqm > 0).map(p => p.pricePerSqm);
        price_bracket_distribution[label] = {
            count: props.length,
            avg_meter: meters.length > 0 ? meters.reduce((a, b) => a + b, 0) / meters.length : 0,
        };
    }

    // Finishing statistics (property type as finishing proxy since we don't have finishing data)
    const finishing_statistics: Record<string, MeterStats> = {};
    const saleTypes = groupBy(valid.filter(p => p.saleType), p => p.saleType);
    for (const [saleType, props] of Object.entries(saleTypes)) {
        finishing_statistics[saleType] = computeMeterStats(props);
    }

    // Summary
    const allMeters = valid.filter(p => p.pricePerSqm > 0).map(p => p.pricePerSqm);
    const allPrices = valid.map(p => p.price);
    const summary = {
        total_properties: valid.length,
        avg_price: allPrices.length > 0 ? allPrices.reduce((a, b) => a + b, 0) / allPrices.length : 0,
        avg_meter: allMeters.length > 0 ? allMeters.reduce((a, b) => a + b, 0) / allMeters.length : 0,
        min_meter: allMeters.length > 0 ? Math.min(...allMeters) : 0,
        max_meter: allMeters.length > 0 ? Math.max(...allMeters) : 0,
        areas_count: Object.keys(meter_price_by_area).length,
        developers_count: Object.keys(meter_price_by_developer).length,
        types_count: Object.keys(meter_price_by_type).length,
    };

    return {
        meter_price_by_area,
        meter_price_by_developer,
        meter_price_by_type,
        room_statistics,
        developer_by_location,
        best_price_per_area,
        best_price_per_developer,
        best_price_per_type,
        finishing_statistics,
        size_bracket_statistics,
        payment_statistics,
        price_bracket_distribution,
        top_compounds,
        summary,
    };
}
