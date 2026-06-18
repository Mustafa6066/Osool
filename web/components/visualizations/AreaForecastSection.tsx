"use client";

/**
 * AreaForecastSection — self-contained fetch+render wrapper for a per-area price
 * forecast. Drop it anywhere with an area name; it slugifies, calls the public
 * /api/forecast/area endpoint (teaser for free users, full for paid), and renders
 * the DESIGN.md-compliant ForecastChart. Renders nothing on error/empty so it can
 * be embedded safely without guarding the parent layout.
 */
import { useEffect, useState } from "react";

import { getAreaForecast, type PriceForecast } from "@/lib/api";
import ForecastChart from "@/components/visualizations/ForecastChart";

export default function AreaForecastSection({ areaName }: { areaName: string }) {
  const [forecast, setForecast] = useState<PriceForecast | null>(null);

  useEffect(() => {
    let alive = true;
    const slug = areaName.toLowerCase().trim().replace(/\s+/g, "-");
    getAreaForecast(slug)
      .then((f) => { if (alive) setForecast(f); })
      .catch(() => { if (alive) setForecast(null); });
    return () => { alive = false; };
  }, [areaName]);

  if (!forecast) return null;
  return <ForecastChart forecast={forecast} />;
}
