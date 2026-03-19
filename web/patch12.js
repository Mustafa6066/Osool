const fs = require('fs');

function globalReplace(file) {
    if (!fs.existsSync(file)) return;
    let code = fs.readFileSync(file, 'utf8');
    
    const prefixes = [' ', '"', "'", '`', ':'];
    const pairs = [
        ['ml-', 'ms-'],
        ['mr-', 'me-'],
        ['pl-', 'ps-'],
        ['pr-', 'pe-'],
        ['left-', 'start-'],
        ['right-', 'end-'],
    ];
    
    let newCode = code;
    for (let p of prefixes) {
        for (let pair of pairs) {
            newCode = newCode.split(p + pair[0]).join(p + pair[1]);
        }
    }
    
    newCode = newCode.split('border-l-').join('border-s-');
    newCode = newCode.split('border-r-').join('border-e-');
    newCode = newCode.split('rounded-l-').join('rounded-s-');
    newCode = newCode.split('rounded-r-').join('rounded-e-');
    newCode = newCode.split('rounded-tl-').join('rounded-ts-');
    newCode = newCode.split('rounded-tr-').join('rounded-te-');
    newCode = newCode.split('rounded-bl-').join('rounded-bs-');
    newCode = newCode.split('rounded-br-').join('rounded-be-');
    newCode = newCode.replace(/\bborder-l\b/g, 'border-s');
    newCode = newCode.replace(/\bborder-r\b/g, 'border-e');
    newCode = newCode.replace(/\btext-left\b/g, 'text-start');
    newCode = newCode.replace(/\btext-right\b/g, 'text-end');

    if (newCode !== code) {
        fs.writeFileSync(file, newCode);
        console.log('Patched ' + file);
    }
}

const files = [
    'd:/Saas/Osool/Osool-Platform/web/components/AgentInterface.tsx',
    'd:/Saas/Osool/Osool-Platform/web/components/dock/LiquidDock.tsx',
    'd:/Saas/Osool/Osool-Platform/web/components/dock/DockContextPanel.tsx',
    'd:/Saas/Osool/Osool-Platform/web/components/LanguageToggle.tsx'
];

for (let f of files) {
    globalReplace(f);
}
