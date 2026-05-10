export type NeuralPhase = 'idle' | 'routing' | 'searching' | 'analyzing' | 'responding' | 'complete' | 'error';

export type NeuralStepStatus = 'active' | 'complete' | 'error';

export interface NeuralSignalStep {
  id: string;
  label: string;
  phase: NeuralPhase;
  status: NeuralStepStatus;
  source?: 'system' | 'stream' | 'tool' | 'local';
  timestamp: number;
}

export interface NeuralSignalSnapshot {
  phase: NeuralPhase;
  steps: NeuralSignalStep[];
  routeLabel: string;
  lastStatus: string;
  intensity: number;
  isLocalPath: boolean;
}

export function inferPhaseFromSignal(signal: string): NeuralPhase {
  const value = signal.toLowerCase();

  if (/error|fail|timeout|تعذر|خطأ|مشكلة/.test(value)) return 'error';
  if (/search|scan|inventory|database|property|listing|عقار|عقارات|بحث|قاعدة/.test(value)) return 'searching';
  if (/analy|score|roi|return|market|price|risk|valuation|benchmark|تحليل|عائد|سعر|مخاطر|تقييم/.test(value)) return 'analyzing';
  if (/token|draft|compose|answer|respond|صياغ|رد/.test(value)) return 'responding';
  if (/route|intent|understand|parse|local|free|طلب|نية/.test(value)) return 'routing';

  return 'analyzing';
}

export function labelForTool(tool: string, language: string): string {
  const lower = tool.toLowerCase();
  const isArabic = language === 'ar';

  if (/search|property|inventory|db|database|vector/.test(lower)) {
    return isArabic ? 'فحص مخزون العقارات' : 'Scanning property inventory';
  }
  if (/market|analytics|price|valuation|roi|score/.test(lower)) {
    return isArabic ? 'تحليل السوق والقيمة' : 'Analyzing market and value';
  }
  if (/risk|legal|law|developer|verification/.test(lower)) {
    return isArabic ? 'مراجعة المخاطر والثقة' : 'Checking risk and trust signals';
  }
  return isArabic ? 'تشغيل أداة التحليل' : 'Running analysis tool';
}

export function initialSignalLabel(language: string): string {
  return language === 'ar' ? 'قراءة نية الطلب' : 'Reading request intent';
}

export function composeSignalLabel(language: string): string {
  return language === 'ar' ? 'صياغة الرد' : 'Composing answer';
}

export function completeSignalLabel(language: string): string {
  return language === 'ar' ? 'التحليل جاهز' : 'Analysis ready';
}

export function errorSignalLabel(language: string): string {
  return language === 'ar' ? 'تعذر إكمال الإشارة' : 'Signal interrupted';
}

export function responseTypeToRouteLabel(responseType: string | undefined, language: string): { label: string; isLocalPath: boolean } {
  const value = (responseType || '').toLowerCase();
  const isArabic = language === 'ar';
  const isLocalPath = /local|free|zero|template|deterministic/.test(value);

  if (isLocalPath) {
    return {
      label: isArabic ? 'مسار محلي بدون توكن' : 'Local zero-token path',
      isLocalPath: true,
    };
  }

  if (/premium|wolf|llm|claude|agent/.test(value)) {
    return {
      label: isArabic ? 'مسار الذكاء الكامل' : 'Full intelligence path',
      isLocalPath: false,
    };
  }

  return {
    label: isArabic ? 'مسار ذكي' : 'Intelligence path',
    isLocalPath: false,
  };
}
