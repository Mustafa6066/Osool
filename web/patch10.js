const fs = require('fs');

function replaceLogicalClasses(filePath) {
    if (!fs.existsSync(filePath)) return;
    let code = fs.readFileSync(filePath, 'utf8');

    const replacements = [
        [/\bml-([0-9\.]+)\b/g, 'ms-$1'],
        [/\bmr-([0-9\.]+)\b/g, 'me-$1'],
        [/\bpl-([0-9\.]+)\b/g, 'ps-$1'],
        [/\bpr-([0-9\.]+)\b/g, 'pe-$1'],
        [/\bleft-([0-9\.]+)\b/g, 'start-$1'],
        [/\bright-([0-9\.]+)\b/g, 'end-$1'],
        [/\bborder-l\b/g, 'border-s'],
        [/\bborder-r\b/g, 'border-e'],
        [/\bborder-l-([a-z0-9\[\]\-]+)\b/g, 'border-s-$1'],
        [/\bborder-r-([a-z0-9\[\]\-]+)\b/g, 'border-e-$1'],
        [/\brounded-l-([a-z0-9\[\]\-]+)\b/g, 'rounded-s-$1'],
        [/\brounded-r-([a-z0-9\[\]\-]+)\b/g, 'rounded-e-$1'],
        [/\brounded-tl-([a-z0-9\[\]\-]+)\b/g, 'rounded-ts-$1'],
        [/\brounded-tr-([a-z0-9\[\]\-]+)\b/g, 'rounded-te-$1'],
        [/\brounded-bl-([a-z0-9\[\]\-]+)\b/g, 'rounded-bs-$1'],
        [/\brounded-br-([a-z0-9\[\]\-]+)\b/g, 'rounded-be-$1'],
        [/\btext-left\b/g, 'text-start'],
        [/\btext-right\b/g, 'text-end'],
    ];

    let newCode = code;
    for (let r of replacements) {
        newCode = newCode.replace(r[0], r[1]);
    }

    if (newCode !== code) {
        fs.writeFileSync(filePath, newCode);
        console.log('Patched ' + filePath);
    }
}

const files = [
    'd:/Saas/Osool/Osool-Platform/web/components/AgentInterface.tsx',
    'd:/Saas/Osool/Osool-Platform/web/components/dock/LiquidDock.tsx',
    'd:/Saas/Osool/Osool-Platform/web/components/dock/DockContextPanel.tsx',
    'd:/Saas/Osool/Osool-Platform/web/components/LanguageToggle.tsx',
];

for (let f of files) {
  replaceLogicalClasses(f);
}
