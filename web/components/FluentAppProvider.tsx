"use client";

import { ReactNode, useMemo } from "react";
import {
  FluentProvider,
  Theme,
  webDarkTheme,
  webLightTheme,
} from "@fluentui/react-components";
import { useTheme } from "@/contexts/ThemeContext";
import { useLanguage } from "@/contexts/LanguageContext";

function buildOsoolTheme(baseTheme: Theme, mode: "light" | "dark"): Theme {
  const brandBase = "#10B981";
  const brandHover = "#059669";
  const brandPressed = "#047857";

  if (mode === "dark") {
    return {
      ...baseTheme,
      colorBrandBackground: brandBase,
      colorBrandBackground2: brandBase,
      colorBrandBackgroundHover: brandHover,
      colorBrandBackgroundPressed: brandPressed,
      colorBrandForeground1: "#34D399",
      colorBrandForeground2: "#10B981",
    };
  }

  return {
    ...baseTheme,
    colorBrandBackground: brandBase,
    colorBrandBackground2: brandBase,
    colorBrandBackgroundHover: brandHover,
    colorBrandBackgroundPressed: brandPressed,
    colorBrandForeground1: "#059669",
    colorBrandForeground2: "#047857",
  };
}

export default function FluentAppProvider({ children }: { children: ReactNode }) {
  const { theme } = useTheme();
  const { direction } = useLanguage();

  const fluentTheme = useMemo(() => {
    if (theme === "dark") {
      return buildOsoolTheme(webDarkTheme, "dark");
    }
    return buildOsoolTheme(webLightTheme, "light");
  }, [theme]);

  return (
    <FluentProvider theme={fluentTheme} dir={direction}>
      {children}
    </FluentProvider>
  );
}