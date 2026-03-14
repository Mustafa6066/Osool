import type { Area, Developer, Project } from '@/lib/seo-api';

export interface PropertyDecisionInput {
  title: string;
  location?: string | null;
  price?: number | null;
  aiEstimate?: number | null;
  bedrooms?: number | null;
  bathrooms?: number | null;
  area?: number | null;
  type?: string | null;
  developer?: string | null;
  saleType?: string | null;
  pricePerSqm?: number | null;
  paymentPlan?: {
    downPayment?: number | null;
    installmentYears?: number | null;
    monthlyInstallment?: number | null;
  } | null;
}

function normalizeRate(value?: number | null): number | null {
  if (value == null || Number.isNaN(value)) {
    return null;
  }
  return value <= 1 ? value * 100 : value;
}

export function formatRate(value?: number | null): string {
  const normalized = normalizeRate(value);
  if (normalized == null) {
    return '—';
  }
  return `${normalized.toFixed(1)}%`;
}

export function formatPriceBand(min?: number | null, max?: number | null): string {
  if (min && max) {
    return `EGP ${Math.round(min).toLocaleString('en-EG')} - ${Math.round(max).toLocaleString('en-EG')} /m²`;
  }
  if (min) {
    return `From EGP ${Math.round(min).toLocaleString('en-EG')} /m²`;
  }
  if (max) {
    return `Up to EGP ${Math.round(max).toLocaleString('en-EG')} /m²`;
  }
  return 'Pricing not available';
}

export function formatCompactPrice(value?: number | null): string {
  if (!value || Number.isNaN(value)) {
    return 'Pricing not available';
  }
  if (value >= 1_000_000) {
    return `EGP ${(value / 1_000_000).toFixed(1)}M`;
  }
  if (value >= 1_000) {
    return `EGP ${(value / 1_000).toFixed(0)}K`;
  }
  return `EGP ${Math.round(value).toLocaleString('en-EG')}`;
}

export function developerBrief(developer: Developer): {
  verdict: string;
  bestFor: string;
  risk: string;
  trustLabel: string;
} {
  const overall = developer.overall_score ?? 0;
  const delivery = developer.avg_delivery_score ?? 0;
  const resale = developer.avg_resale_retention ?? 0;
  const payments = developer.payment_flexibility ?? 0;

  let verdict = 'Balanced developer with no single dominant edge.';
  if (delivery >= 88) {
    verdict = 'High-confidence delivery profile with lower execution anxiety.';
  } else if (resale >= 85) {
    verdict = 'Strong brand and resale resilience for investors who value exit quality.';
  } else if (payments >= 85) {
    verdict = 'Flexible payment structure can lower entry pressure.';
  }

  let bestFor = 'Balanced buyers who want a broad market benchmark.';
  if (delivery >= 88) {
    bestFor = 'Trust-first buyers who care about delivery discipline.';
  } else if (resale >= 85) {
    bestFor = 'Investors optimizing for long-term liquidity and brand premium.';
  } else if (payments >= 85) {
    bestFor = 'Buyers who need easier payment entry and flexibility.';
  }

  const risk =
    overall >= 85
      ? 'Main risk is paying up for a premium name rather than operational trust.'
      : 'Review project-level execution and payment details before treating this as a safe default.';

  const trustLabel =
    overall >= 90 ? 'Institutional trust tier' : overall >= 80 ? 'High-confidence tier' : overall >= 70 ? 'Selective confidence tier' : 'Needs more diligence';

  return { verdict, bestFor, risk, trustLabel };
}

export function areaBrief(area: Area): {
  thesis: string;
  bestFor: string;
  risk: string;
  strategy: string;
} {
  const yieldRate = normalizeRate(area.rental_yield) ?? 0;
  const growthRate = normalizeRate(area.price_growth_ytd) ?? 0;
  const liquidity = area.liquidity_score ?? 0;
  const demand = area.demand_score ?? 0;

  let strategy = 'Balanced';
  let thesis = 'Balanced corridor with mixed upside across income and appreciation.';
  let bestFor = 'Buyers who want a diversified starting point.';

  if (yieldRate >= 8) {
    strategy = 'Yield-led';
    thesis = 'Rental economics lead the story here more than rapid speculative upside.';
    bestFor = 'Income-oriented investors who want steadier occupancy and cash flow.';
  } else if (growthRate >= 12) {
    strategy = 'Appreciation-led';
    thesis = 'Capital growth is the main attraction, with price momentum doing most of the work.';
    bestFor = 'Investors focused on medium-term appreciation over immediate rental yield.';
  } else if (liquidity >= 80 || demand >= 80) {
    strategy = 'Stability-led';
    thesis = 'Demand and liquidity make this a steadier place to enter without chasing extremes.';
    bestFor = 'Conservative buyers prioritizing market depth and lower exit friction.';
  }

  const risk =
    growthRate >= 12
      ? 'Fast growth can hide bad entry pricing, so selection matters more than the headline trend.'
      : yieldRate >= 8
        ? 'Yield stories still need project-level validation on vacancy, finishes, and service costs.'
        : 'Use project quality and developer trust to avoid treating the whole area as equally attractive.';

  return { thesis, bestFor, risk, strategy };
}

export function projectBrief(project: Project): {
  thesis: string;
  bestFor: string;
  risk: string;
} {
  const down = project.down_payment_min ?? 100;
  const years = project.installment_years ?? 0;
  const roi5 = normalizeRate(project.predicted_roi_5y) ?? 0;
  const progress = project.construction_progress ?? 0;

  let thesis = 'Project worth evaluating through location, payment fit, and developer quality.';
  let bestFor = 'Buyers who want a broad project benchmark before going deeper.';

  if (down <= 10 && years >= 8) {
    thesis = 'Payment structure is the main reason this project stands out.';
    bestFor = 'Buyers who need a lower-friction entry and longer cash-flow runway.';
  } else if (roi5 >= 45) {
    thesis = 'Projected upside makes this more interesting as a medium-term investment play.';
    bestFor = 'Investors prioritizing appreciation potential over immediate income.';
  } else if (progress >= 60) {
    thesis = 'Execution progress reduces uncertainty relative to early-stage alternatives.';
    bestFor = 'Trust-first buyers who want more visible delivery momentum.';
  }

  const risk =
    progress > 0 && progress < 40
      ? 'Early execution means timelines and pricing assumptions need closer scrutiny.'
      : down <= 10 && years >= 8
        ? 'Flexible terms help, but they should not distract from pricing quality and delivery risk.'
        : 'Validate the developer, area, and delivery reality before treating this as a default option.';

  return { thesis, bestFor, risk };
}

export function propertyBrief(property: PropertyDecisionInput): {
  thesis: string;
  bestFor: string;
  risk: string;
  confidenceLabel: string;
  priceSignal: string;
} {
  const price = property.price ?? 0;
  const aiEstimate = property.aiEstimate ?? 0;
  const priceGapPct = price > 0 && aiEstimate > 0 ? ((aiEstimate - price) / price) * 100 : null;
  const downPayment = property.paymentPlan?.downPayment ?? null;
  const installmentYears = property.paymentPlan?.installmentYears ?? null;
  const monthlyInstallment = property.paymentPlan?.monthlyInstallment ?? null;
  const isResale = (property.saleType || '').toLowerCase() === 'resale';
  const bedrooms = property.bedrooms ?? 0;
  const type = (property.type || '').toLowerCase();

  let thesis = 'Worth reviewing through price quality, delivery confidence, and payment fit.';
  let bestFor = 'Buyers who want a shortlist candidate before deeper advisor work.';
  let risk = 'Validate developer quality, area pricing, and total ownership cost before moving forward.';
  let confidenceLabel = 'Needs review';
  let priceSignal = 'No valuation signal yet';

  if (priceGapPct != null) {
    if (priceGapPct >= 5) {
      thesis = 'Looks attractively priced relative to the current valuation signal.';
      bestFor = 'Value-oriented buyers who want a better entry point than the surrounding market.';
      confidenceLabel = 'Value pocket';
      priceSignal = `${priceGapPct.toFixed(1)}% below AI estimate`;
      risk = 'A discount can still hide quality or liquidity issues, so verify the reason for the pricing gap.';
    } else if (priceGapPct <= -5) {
      thesis = 'Pricing looks stretched versus the current valuation signal.';
      bestFor = 'Buyers with strong conviction on location or developer premium.';
      confidenceLabel = 'Premium entry';
      priceSignal = `${Math.abs(priceGapPct).toFixed(1)}% above AI estimate`;
      risk = 'You may be paying ahead of fundamentals, so compare this against nearby alternatives before acting.';
    } else {
      confidenceLabel = 'Fair-value range';
      priceSignal = 'Close to valuation range';
    }
  }

  if (downPayment != null && installmentYears != null && downPayment <= 10 && installmentYears >= 8) {
    thesis = 'The payment plan is the main reason to keep this on the board.';
    bestFor = 'Buyers who need lower upfront cash and a longer runway on installments.';
    confidenceLabel = 'Plan-friendly';
    priceSignal = monthlyInstallment ? `${downPayment}% down with ${installmentYears} years` : `${downPayment}% down payment`;
    risk = 'Flexible plans help cash flow, but they should not override pricing quality or developer risk.';
  } else if (isResale) {
    thesis = 'Resale status can reduce delivery uncertainty and speed up a use or exit decision.';
    bestFor = 'Buyers who want more immediate clarity on handover and livability.';
    confidenceLabel = 'Ready-now angle';
    priceSignal = priceGapPct == null ? 'Resale timing advantage' : priceSignal;
    risk = 'Resale convenience does not replace diligence on finish quality, service costs, or legal cleanliness.';
  } else if (bedrooms >= 3 || type.includes('villa') || type.includes('townhouse') || type.includes('duplex')) {
    thesis = 'This reads more like a family-use or long-hold decision than a pure quick-flip play.';
    bestFor = 'End-users or long-hold buyers prioritizing space and stability.';
    confidenceLabel = 'Family-fit';
    risk = 'Make sure layout, delivery confidence, and monthly burden still justify the larger ticket.';
  }

  return { thesis, bestFor, risk, confidenceLabel, priceSignal };
}

export function buildAdvisorPrompt(property: PropertyDecisionInput): string {
  const fragments = [
    `Review this property for me: ${property.title}`,
    property.location ? `in ${property.location}` : '',
    property.price ? `priced at ${formatCompactPrice(property.price)}` : '',
    property.type ? `(${property.type})` : '',
  ].filter(Boolean);

  const extras = [
    property.developer ? `Developer: ${property.developer}.` : '',
    property.pricePerSqm ? `Price per sqm: ${Math.round(property.pricePerSqm).toLocaleString('en-EG')} EGP.` : '',
    property.aiEstimate ? `AI estimate: ${formatCompactPrice(property.aiEstimate)}.` : '',
    property.paymentPlan?.downPayment != null && property.paymentPlan?.installmentYears != null
      ? `Payment plan: ${property.paymentPlan.downPayment}% down over ${property.paymentPlan.installmentYears} years.`
      : '',
  ].filter(Boolean);

  return `${fragments.join(' ')}. Tell me whether it looks fairly priced, who it suits best, the main risks, and whether I should shortlist it.` + (extras.length > 0 ? ` ${extras.join(' ')}` : '');
}

export function pickWinnerLabel(v1: number, v2: number, label1: string, label2: string): string {
  if (v1 > v2) {
    return label1;
  }
  if (v2 > v1) {
    return label2;
  }
  return 'Tie';
}