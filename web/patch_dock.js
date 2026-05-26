const fs = require('fs');
let code = fs.readFileSync('components/dock/LiquidDock.tsx', 'utf8');

const oldBtn = 'className="relative flex items-center justify-center w-11 h-11 rounded-2xl focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50"';
const newBtn = 'className={`relative overflow-hidden flex items-center justify-center h-[52px] sm:h-11 rounded-2xl focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50 ${isActive ? \'w-[100px] sm:w-[120px] px-4\' : \'w-[52px] sm:w-11 px-0\'}`}';

code = code.replace(oldBtn, newBtn);

const oldIcon = `<Icon
                    className={\`w-[22px] h-[22px] transition-colors duration-200 \${
                      isActive
                        ? 'text-emerald-500'
                        : 'text-[var(--color-text-muted)] group-hover:text-[var(--color-text-primary)]'
                    }\`}
                    strokeWidth={isActive ? 2.4 : 1.6}
                  />`;

const newIcon = `<Icon
                    className={\`w-[22px] h-[22px] shrink-0 transition-colors duration-200 \${
                      isActive
                        ? 'text-emerald-500'
                        : 'text-[var(--color-text-muted)] group-hover:text-[var(--color-text-primary)]'
                    }\`}
                    strokeWidth={isActive ? 2.4 : 1.6}
                  />
                  <AnimatePresence>
                  {isActive && (
                    <motion.span
                      initial={{ width: 0, opacity: 0, marginInlineStart: 0 }}
                      animate={{ width: 'auto', opacity: 1, marginInlineStart: 8 }}
                      exit={{ width: 0, opacity: 0, marginInlineStart: 0 }}
                      transition={{ duration: 0.2 }}
                      className="font-medium text-[13px] text-emerald-500 whitespace-nowrap overflow-hidden hidden sm:block"
                    >
                      {language === 'ar' ? item.labelAr : item.label}
                    </motion.span>
                  )}
                  </AnimatePresence>`;

code = code.replace(oldIcon, newIcon);

fs.writeFileSync('components/dock/LiquidDock.tsx', code, 'utf8');
