const fs = require('fs');

function replaceClass(code, oldPrefix, newPrefix) {
    const rx = new RegExp(`(?<=[\\s"'\\\`:])` + oldPrefix + `-([^\\s" '\\\`]+)`, 'g');
    return code.replace(rx, newPrefix + '-$1');
}

function replaceLogicalClasses(filePath) {
    if (!fs.existsSync(filePath)) return;
    let code = fs.readFileSync(filePath, 'utf8');
    
    let newCode = code;
    newCode = replaceClass(newCode, 'ml', 'ms');
    newCode = replaceClass(newCode, '-ml', '-ms');
    newCode = replaceClass(newCode, 'mr', 'me');
    newCode = replaceClass(newCode, '-mr', '-me');
    newCode = replaceClass(newCode, 'pl', 'ps');
    newCode = replaceClass(newCode, 'pr', 'pe');
    newCode = replaceClass(newCode, 'left', 'start');
    newCode = replaceClass(newCode, '-left', '-start');
    newCode = replaceClass(newCode, 'right', 'end');
    newCode = replaceClass(newCode, '-right', '-end');
    newCode = replaceClass(newCode, 'border-l', 'border-s');
    newCode = replaceClass(newCode, 'border-r', 'border-e');
    newCode = replaceClass(newCode, 'rounded-l', 'rounded-s');
    newCode = replaceClass(newCode, 'rounded-r', 'rounded-e');
    newCode = replaceClass(newCode, 'rounded-tl', 'rounded-ts');
    newCode = replaceClass(newCode, 'rounded-tr', 'rounded-te');
    newCode = replaceClass(newCode, 'rounded-bl', 'rounded-bs');
    newCode = replaceClass(newCode, 'rounded-br', 'rounded-be');
    
    // Also exact words
    newCode = newCode.replace(/(?<=[\s"'\`:])text-left(?=[\s"'\`])/g, 'text-start');
    newCode = newCode.replace(/(?<=[\s"'\`:])text-right(?=[\s"'\`])/g, 'text-end');
    newCode = newCode.replace(/(?<=[\s"'\`:])border-l(?=[\s"'\`])/g, 'border-s');
    newCode = newCode.replace(/(?<=[\s"'\`:])border-r(?=[\s"'\`])/g, 'border-e');

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
    'd:/Saas/Osool/Osool-Platform/web/components/dock/Dock.tsx'
];

for (let f of files) {
  replaceLogicalClasses(f);
}
