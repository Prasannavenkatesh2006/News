const fs = require('fs');
const path = require('path');

function walk(dir, done) {
    let results = [];
    fs.readdir(dir, function(err, list) {
        if (err) return done(err);
        let pending = list.length;
        if (!pending) return done(null, results);
        list.forEach(function(file) {
            file = path.resolve(dir, file);
            fs.stat(file, function(err, stat) {
                if (stat && stat.isDirectory()) {
                    walk(file, function(err, res) {
                        results = results.concat(res);
                        if (!--pending) done(null, results);
                    });
                } else {
                    if (file.endsWith('.ts') || file.endsWith('.tsx')) {
                        results.push(file);
                    }
                    if (!--pending) done(null, results);
                }
            });
        });
    });
}

function checkImports() {
    const frontendDir = path.resolve(process.cwd(), 'frontend');
    walk(frontendDir, (err, files) => {
        if (err) throw err;
        let errors = 0;
        files.forEach(file => {
            const content = fs.readFileSync(file, 'utf8');
            const lines = content.split('\n');
            lines.forEach((line, i) => {
                const match = line.match(/from\s+['"]([^'"]+)['"]/);
                if (match) {
                    let importPath = match[1];
                    if (importPath.startsWith('.')) {
                        const dir = path.dirname(file);
                        let resolvedPath = path.resolve(dir, importPath);
                        // Check if file exists exactly as written (case-sensitive simulation)
                        // In windows, fs.existsSync is case-insensitive, so we have to check readdir
                        
                        // Let's resolve the actual file name
                        let targetDir = path.dirname(resolvedPath);
                        let targetBase = path.basename(resolvedPath);
                        
                        if (fs.existsSync(targetDir)) {
                            const actualFiles = fs.readdirSync(targetDir);
                            
                            // Try to find exact match with extensions
                            const extensions = ['', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.tsx'];
                            let found = false;
                            
                            for (let ext of extensions) {
                                if (actualFiles.includes(targetBase + ext)) {
                                    found = true;
                                    break;
                                }
                            }
                            
                            if (!found) {
                                // Check if it's case insensitive match
                                const lowerBase = targetBase.toLowerCase();
                                const caseMismatches = actualFiles.filter(f => f.toLowerCase() === lowerBase || f.toLowerCase() === lowerBase + '.tsx' || f.toLowerCase() === lowerBase + '.ts');
                                
                                if (caseMismatches.length > 0) {
                                    console.log(`❌ Case mismatch in ${file}:${i+1}`);
                                    console.log(`   Imported: '${importPath}'`);
                                    console.log(`   Actual file(s): ${caseMismatches.join(', ')}`);
                                    errors++;
                                }
                            }
                        }
                    }
                }
            });
        });
        console.log(`Found ${errors} potential case-sensitivity errors.`);
    });
}

checkImports();
