
document.addEventListener('DOMContentLoaded', function () {
    initMap();
});

function initMap() {
    const mapElement = document.getElementById('mapContainer');
    if (!mapElement) return;

    // Center on New Cairo
    const map = L.map('mapContainer').setView([30.0074, 31.4913], 12);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    // Generated Coordinates Logic
    // Since Excel data doesn't include GPS, we approximate based on real location names
    const areaCenters = {
        "New Cairo": { lat: 30.0074, lng: 31.4913 },
        "6th settlement": { lat: 30.0300, lng: 31.5200 }, // Approx
        "Mostakbal City": { lat: 30.1300, lng: 31.6000 },
        "Golden Square": { lat: 30.0250, lng: 31.4800 },
        "Madinaty": { lat: 30.0900, lng: 31.6300 },
        "South New Cairo": { lat: 29.9800, lng: 31.4500 }
    };

    // Helper to generate random offset
    function offset(coord) {
        return coord + (Math.random() - 0.5) * 0.04;
    }

    if (window.egyptianData && window.egyptianData.properties) {
        window.egyptianData.properties.forEach(prop => {
            let center = areaCenters[prop.location] || areaCenters["New Cairo"];

            // Assign coords if missing
            if (!prop.lat) {
                prop.lat = offset(center.lat);
                prop.lng = offset(center.lng);
            }

            // Create Marker
            const marker = L.marker([prop.lat, prop.lng]).addTo(map);

            // bind popup
            const popupContent = `
                <div style="font-family: 'Inter', sans-serif; text-align: right; min-width: 200px;">
                    <img src="${prop.image}" style="width: 100%; height: 120px; object-fit: cover; border-radius: 8px; margin-bottom: 8px;">
                    <h4 style="margin: 0 0 4px; font-size: 14px;">${prop.compound}</h4>
                    <div style="font-size: 12px; color: #666;">${prop.location}</div>
                    <div style="font-weight: bold; color: #059669; margin-top: 4px;">${prop.price.toLocaleString()} EGP</div>
                    <button onclick="document.getElementById('chatInput').value='تفاصيل عن ${prop.compound}'; sendMessage();" 
                        style="background: #059669; color: white; border: none; width: 100%; padding: 6px; border-radius: 4px; margin-top: 8px; cursor: pointer;">
                        اسأل عمرو
                    </button>
                </div>
            `;

            marker.bindPopup(popupContent);
        });
    }
}
