/**
 * Financial Comparison Table Examples
 * Real-world usage examples for the table rendering components
 */

import { 
  DataTable, 
  FinancialComparisonTable,
  BankVsPropertyComparisonTable,
  tableFormatters 
} from '@/components/visualizations';

/**
 * Example 1: Bank vs Property Comparison (from attachment image)
 * العائد الشهري vs العائد الحقيقي (على 5 مليون جنيه)
 */
export function BankVsPropertyExample() {
  return (
    <BankVsPropertyComparisonTable
      bankMonthly={8.4}           // % العائد الشهري للبنك
      bankActual={13.6}           // % العائد الحقيقي للبنك
      propertyMonthly={16.8}      // % العائد الشهري للعقار (شقة درك)
      propertyActual={13.6}       // % العائد الحقيقي للعقار
      isRTL={true}
    />
  );
}

/**
 * Example 2: Complex Financial Comparison
 * Multiple investment scenarios
 */
export function MultipleInvestmentComparison() {
  const rows = [
    {
      label: 'الكاش (على 5 مليون جنيه)',
      icon: '💰',
      values: [
        {
          name: 'البنك البيضاء',
          value: 8.4,
          change: -13.6,
          trend: 'neutral' as const,
          color: 'text-yellow-400'
        },
        {
          name: 'شقة درك',
          value: 16.8,
          change: 13.6,
          trend: 'up' as const,
          color: 'text-green-400'
        }
      ]
    },
    {
      label: '% العائد الحقيقي',
      icon: '📊',
      values: [
        {
          name: 'البنك البيضاء',
          value: 13.6,
          change: 0,
          trend: 'neutral' as const,
          color: 'text-yellow-400'
        },
        {
          name: 'شقة درك',
          value: 13.6,
          change: -13.6,
          trend: 'down' as const,
          color: 'text-red-400'
        }
      ]
    },
    {
      label: '✅ شقة درك',
      icon: '🏠',
      values: [
        {
          name: 'البنك البيضاء',
          value: '❌ لا',
          trend: 'neutral' as const,
          color: 'text-red-400'
        },
        {
          name: 'شقة درك',
          value: '✅ نعم',
          trend: 'up' as const,
          color: 'text-green-400'
        }
      ]
    },
    {
      label: '🏗️ عمار (لمو إسكندر)',
      icon: '🏢',
      values: [
        {
          name: 'البنك البيضاء',
          value: 30.4,
          change: 22,
          trend: 'up' as const,
          color: 'text-green-400'
        },
        {
          name: 'شقة درك',
          value: 7.5,
          change: -6.1,
          trend: 'down' as const,
          color: 'text-red-400'
        }
      ]
    },
    {
      label: '🏗️ عمار فقط',
      icon: '🏢',
      values: [
        {
          name: 'البنك البيضاء',
          value: 6.1,
          change: -2.3,
          trend: 'down' as const,
          color: 'text-red-400'
        },
        {
          name: 'شقة درك',
          value: 7.5,
          change: 1.4,
          trend: 'up' as const,
          color: 'text-green-400'
        }
      ]
    }
  ];

  return (
    <FinancialComparisonTable
      title="مقارنة شاملة - العائد الشهري vs العائد الحقيقي"
      subtitle="على 5 مليون جنيه - All scenarios"
      rows={rows}
      isRTL={true}
      colorScheme="info"
      showTrends={true}
    />
  );
}

/**
 * Example 3: Property Comparison Data Table
 * Listing properties with detailed metrics
 */
export function PropertyComparisonTable() {
  const columns = [
    {
      key: 'compound',
      header: 'المركب',
      align: 'right' as const,
      width: '180px'
    },
    {
      key: 'location',
      header: 'الموقع',
      align: 'center' as const,
      width: '150px'
    },
    {
      key: 'bedrooms',
      header: 'الغرف',
      align: 'center' as const,
      width: '80px'
    },
    {
      key: 'area',
      header: 'المساحة',
      align: 'center' as const,
      format: tableFormatters.area
    },
    {
      key: 'price',
      header: 'السعر',
      align: 'center' as const,
      format: tableFormatters.currency
    },
    {
      key: 'price_per_sqm',
      header: 'سعر/م²',
      align: 'center' as const,
      format: tableFormatters.currency
    },
    {
      key: 'roi',
      header: 'العائد',
      align: 'center' as const,
      format: tableFormatters.roi
    },
    {
      key: 'delivered',
      header: 'حالة التسليم',
      align: 'center' as const,
      format: tableFormatters.yesNo
    }
  ];

  const data = [
    {
      compound: 'شقة درك',
      location: 'الرحاب',
      bedrooms: 2,
      area: 150,
      price: 2500000,
      price_per_sqm: 16667,
      roi: 12.5,
      delivered: true
    },
    {
      compound: 'فيلا درك',
      location: 'الرحاب',
      bedrooms: 4,
      area: 320,
      price: 5000000,
      price_per_sqm: 15625,
      roi: 14.2,
      delivered: true
    },
    {
      compound: 'عمار لمو',
      location: 'الإسكندرية',
      bedrooms: 2,
      area: 140,
      price: 1800000,
      price_per_sqm: 12857,
      roi: 18.5,
      delivered: false
    },
    {
      compound: 'عمار سكاي',
      location: 'المقطم',
      bedrooms: 3,
      area: 200,
      price: 3200000,
      price_per_sqm: 16000,
      roi: 11.2,
      delivered: false
    }
  ];

  return (
    <DataTable
      title="مقارنة العقارات المتاحة"
      subtitle="أفضل الخيارات المتاحة الآن"
      columns={columns}
      data={data}
      isRTL={true}
      sortable={true}
      defaultSortKey="roi"
      defaultSortOrder="desc"
      colorScheme="primary"
      icon="🏠"
    />
  );
}

/**
 * Example 4: Payment Plans Comparison
 * Different financing options for same property
 */
export function PaymentPlansComparison() {
  const columns = [
    {
      key: 'plan_name',
      header: 'نوع الخطة',
      align: 'right' as const
    },
    {
      key: 'total_price',
      header: 'السعر الكلي',
      align: 'center' as const,
      format: tableFormatters.currency
    },
    {
      key: 'down_payment_percent',
      header: '% المقدم',
      align: 'center' as const,
      format: (v: number) => `${v}%`
    },
    {
      key: 'down_payment_amount',
      header: 'قيمة المقدم',
      align: 'center' as const,
      format: tableFormatters.currency
    },
    {
      key: 'installment_years',
      header: 'المدة',
      align: 'center' as const,
      format: (v: number) => `${v} سنوات`
    },
    {
      key: 'monthly_installment',
      header: 'القسط الشهري',
      align: 'center' as const,
      format: tableFormatters.currency
    },
    {
      key: 'total_paid',
      header: 'الإجمالي المدفوع',
      align: 'center' as const,
      format: tableFormatters.currency
    }
  ];

  const data = [
    {
      plan_name: 'كاش فوري',
      total_price: 2500000,
      down_payment_percent: 100,
      down_payment_amount: 2500000,
      installment_years: 0,
      monthly_installment: 0,
      total_paid: 2500000
    },
    {
      plan_name: 'مقدم 30% (سنتين)',
      total_price: 2500000,
      down_payment_percent: 30,
      down_payment_amount: 750000,
      installment_years: 2,
      monthly_installment: 91667,
      total_paid: 2500000
    },
    {
      plan_name: 'مقدم 20% (خمس سنين)',
      total_price: 2500000,
      down_payment_percent: 20,
      down_payment_amount: 500000,
      installment_years: 5,
      monthly_installment: 41667,
      total_paid: 2500000
    },
    {
      plan_name: 'مقدم 10% (عشر سنين)',
      total_price: 2500000,
      down_payment_percent: 10,
      down_payment_amount: 250000,
      installment_years: 10,
      monthly_installment: 20833,
      total_paid: 2500000
    }
  ];

  return (
    <DataTable
      title="خطط السداد المتاحة"
      subtitle="شقة درك - الرحاب - 2,500,000 ج"
      columns={columns}
      data={data}
      isRTL={true}
      sortable={true}
      defaultSortKey="monthly_installment"
      defaultSortOrder="asc"
      colorScheme="success"
      icon="💳"
      maxHeight="500px"
    />
  );
}

/**
 * Example 5: Market Analysis Data Table
 * Area-by-area market statistics
 */
export function MarketAnalysisTable() {
  const columns = [
    {
      key: 'area',
      header: 'المنطقة',
      align: 'right' as const
    },
    {
      key: 'avg_price',
      header: 'متوسط السعر',
      align: 'center' as const,
      format: tableFormatters.currency
    },
    {
      key: 'avg_price_sqm',
      header: 'ج/م²',
      align: 'center' as const,
      format: tableFormatters.currency
    },
    {
      key: 'supply',
      header: 'العروض',
      align: 'center' as const,
      format: tableFormatters.number
    },
    {
      key: 'growth_yoy',
      header: 'النمو السنوي',
      align: 'center' as const,
      format: tableFormatters.percentageWithTrend
    },
    {
      key: 'demand',
      header: 'الطلب',
      align: 'center' as const,
      format: (v: string) => (
        <span className={v === 'عالي' ? 'text-green-400' : v === 'متوسط' ? 'text-yellow-400' : 'text-red-400'}>
          {v}
        </span>
      )
    }
  ];

  const data = [
    {
      area: 'الرحاب',
      avg_price: 2800000,
      avg_price_sqm: 18667,
      supply: 245,
      growth_yoy: 0.18,
      demand: 'عالي'
    },
    {
      area: 'المقطم',
      avg_price: 3200000,
      avg_price_sqm: 16000,
      supply: 189,
      growth_yoy: 0.22,
      demand: 'عالي'
    },
    {
      area: 'التجمع الخامس',
      avg_price: 3500000,
      avg_price_sqm: 17500,
      supply: 312,
      growth_yoy: 0.15,
      demand: 'متوسط'
    },
    {
      area: 'الشيخ زايد',
      avg_price: 2400000,
      avg_price_sqm: 16000,
      supply: 156,
      growth_yoy: -0.05,
      demand: 'منخفض'
    }
  ];

  return (
    <DataTable
      title="تحليل السوق حسب المنطقة"
      subtitle="آخر تحديث - مارس 2026"
      columns={columns}
      data={data}
      isRTL={true}
      sortable={true}
      defaultSortKey="growth_yoy"
      defaultSortOrder="desc"
      colorScheme="warning"
      icon="📈"
    />
  );
}

/**
 * Usage in a React Component
 */
export function FinancialComparisonPage() {
  return (
    <div className="space-y-8 p-6">
      <h1 className="text-3xl font-bold text-white mb-8">
        🏠 أدوات المقارنة المالية
      </h1>

      {/* Bank vs Property */}
      <section>
        <h2 className="text-xl font-semibold text-white mb-4">
          البنك ضد العقار
        </h2>
        <BankVsPropertyExample />
      </section>

      {/* Multiple Comparisons */}
      <section>
        <h2 className="text-xl font-semibold text-white mb-4">
          جميع السيناريوهات
        </h2>
        <MultipleInvestmentComparison />
      </section>

      {/* Property Comparison */}
      <section>
        <h2 className="text-xl font-semibold text-white mb-4">
          مقارنة العقارات
        </h2>
        <PropertyComparisonTable />
      </section>

      {/* Payment Plans */}
      <section>
        <h2 className="text-xl font-semibold text-white mb-4">
          خطط الدفع
        </h2>
        <PaymentPlansComparison />
      </section>

      {/* Market Analysis */}
      <section>
        <h2 className="text-xl font-semibold text-white mb-4">
          تحليل السوق
        </h2>
        <MarketAnalysisTable />
      </section>
    </div>
  );
}
