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
  // Osool terracotta brand ramp (mirrors --osool-accent tokens in osool-theme.css).
  // Fluent's Theme is a plain JS object, so CSS vars can't be referenced here — use hex literals.
  const brandBase = "#C96442"; // --osool-accent (light)
  const brandHover = "#B5512F"; // --osool-accent-dark (light)
  const brandPressed = "#9A4427"; // pressed terracotta (deeper than -dark)

  if (mode === "dark") {
    return {
      ...baseTheme,
      colorBrandBackground: brandBase,
      colorBrandBackground2: brandBase,
      colorBrandBackgroundHover: brandHover,
      colorBrandBackgroundPressed: brandPressed,
      colorBrandForeground1: "#D87555", // --osool-accent (dark)
      colorBrandForeground2: "#C96442",
    };
  }

  return {
    ...baseTheme,
    colorBrandBackground: brandBase,
    colorBrandBackground2: brandBase,
    colorBrandBackgroundHover: brandHover,
    colorBrandBackgroundPressed: brandPressed,
    colorBrandForeground1: "#B5512F",
    colorBrandForeground2: "#9A4427",
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