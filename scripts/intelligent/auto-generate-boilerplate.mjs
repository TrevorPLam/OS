#!/usr/bin/env node
// Auto-Generate Boilerplate Code
// Usage: node scripts/intelligent/auto-generate-boilerplate.mjs --type component|screen|api|feature [--name Name] [--path path/to/dir]

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const TYPE = process.argv.find((arg) => arg.startsWith("--type="))?.split("=")[1];
const NAME = process.argv.find((arg) => arg.startsWith("--name="))?.split("=")[1];
const TARGET_PATH = process.argv.find((arg) => arg.startsWith("--path="))?.split("=")[1] || ".";

function generateComponent(name, targetDir) {
  const componentName = name.charAt(0).toUpperCase() + name.slice(1);
  const fileName = `${componentName}.tsx`;
  const filePath = path.join(targetDir, fileName);

  const content = `import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface ${componentName}Props {
  // TODO: Add props
}

export const ${componentName}: React.FC<${componentName}Props> = (props) => {
  return (
    <View style={styles.container}>
      <Text>${componentName}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    // TODO: Add styles
  },
});
`;

  return { filePath, content, testPath: path.join(targetDir, `${componentName}.test.tsx`) };
}

function generateScreen(name, targetDir) {
  const screenName = `${name}Screen`;
  const fileName = `${screenName}.tsx`;
  const filePath = path.join(targetDir, fileName);

  const content = `import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';

export const ${screenName}: React.FC = () => {
  const navigation = useNavigation();

  return (
    <View style={styles.container}>
      <Text>${screenName}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
});
`;

  return { filePath, content };
}

function generateAPIEndpoint(name, targetDir) {
  const endpointName = name.toLowerCase();
  const fileName = `${endpointName}.ts`;
  const filePath = path.join(targetDir, fileName);

  const content = `import { Request, Response } from 'express';
import { z } from 'zod';

// Request schema
const ${endpointName}Schema = z.object({
  // TODO: Add request schema
});

export const ${endpointName}Handler = async (req: Request, res: Response) => {
  try {
    // Validate request
    const validated = ${endpointName}Schema.parse(req.body);

    // TODO: Implement handler logic

    res.json({ success: true });
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: error.errors });
      return;
    }
    res.status(500).json({ error: 'Internal server error' });
  }
};
`;

  return { filePath, content };
}

function generateFeature(name, targetDir) {
  const featureName = name.charAt(0).toUpperCase() + name.slice(1);
  const featureDir = path.join(targetDir, featureName.toLowerCase());

  const structure = {
    [`${featureName}Screen.tsx`]: generateScreen(name, featureDir).content,
    [`components/${featureName}Component.tsx`]: generateComponent(name, path.join(featureDir, "components")).content,
    [`hooks/use${featureName}.ts`]: `import { useState } from 'react';

export const use${featureName} = () => {
  const [state, setState] = useState(null);

  // TODO: Implement hook logic

  return { state, setState };
};
`,
    [`index.ts`]: `export * from './${featureName}Screen';
export * from './components';
export * from './hooks';
`,
  };

  return { featureDir, structure };
}

function main() {
  console.log("🏗️  Auto-Generate Boilerplate Code\n");

  if (!TYPE || !NAME) {
    console.error("❌ Type and name required");
    console.log("   Usage: --type=component|screen|api|feature --name=Name");
    process.exit(1);
  }

  const targetDir = path.resolve(REPO_ROOT, TARGET_PATH);
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }

  console.log(`📦 Type: ${TYPE}`);
  console.log(`📝 Name: ${NAME}`);
  console.log(`📁 Target: ${path.relative(REPO_ROOT, targetDir)}\n`);

  let result;

  switch (TYPE) {
    case "component":
      result = generateComponent(NAME, targetDir);
      break;
    case "screen":
      result = generateScreen(NAME, targetDir);
      break;
    case "api":
      result = generateAPIEndpoint(NAME, targetDir);
      break;
    case "feature":
      result = generateFeature(NAME, targetDir);
      break;
    default:
      console.error(`❌ Unknown type: ${TYPE}`);
      console.log("   Supported types: component, screen, api, feature");
      process.exit(1);
  }

  if (TYPE === "feature") {
    // Create feature directory structure
    fs.mkdirSync(result.featureDir, { recursive: true });
    fs.mkdirSync(path.join(result.featureDir, "components"), { recursive: true });
    fs.mkdirSync(path.join(result.featureDir, "hooks"), { recursive: true });

    for (const [file, content] of Object.entries(result.structure)) {
      const filePath = path.join(result.featureDir, file);
      const fileDir = path.dirname(filePath);
      if (!fs.existsSync(fileDir)) {
        fs.mkdirSync(fileDir, { recursive: true });
      }
      fs.writeFileSync(filePath, content);
      console.log(`✅ Created: ${path.relative(REPO_ROOT, filePath)}`);
    }
  } else {
    fs.writeFileSync(result.filePath, result.content);
    console.log(`✅ Created: ${path.relative(REPO_ROOT, result.filePath)}`);

    if (result.testPath && TYPE === "component") {
      // Generate test file
      const testContent = `import { render, screen } from '@testing-library/react-native';
import { ${NAME.charAt(0).toUpperCase() + NAME.slice(1)} } from './${NAME.charAt(0).toUpperCase() + NAME.slice(1)}';

describe('${NAME.charAt(0).toUpperCase() + NAME.slice(1)}', () => {
  it('should render correctly', () => {
    render(<${NAME.charAt(0).toUpperCase() + NAME.slice(1)} />);
    expect(screen.getByText('${NAME.charAt(0).toUpperCase() + NAME.slice(1)}')).toBeDefined();
  });
});
`;
      fs.writeFileSync(result.testPath, testContent);
      console.log(`✅ Created: ${path.relative(REPO_ROOT, result.testPath)}`);
    }
  }

  console.log(`\n✅ Boilerplate generated successfully!`);
}

main();
