"use client";

import { useEffect } from "react";

type TelegramWebApp = {
  ready: () => void;
  expand: () => void;
  setHeaderColor?: (color: string) => void;
  setBackgroundColor?: (color: string) => void;
  colorScheme?: "light" | "dark";
  themeParams?: Record<string, string>;
};

function applyTheme(webApp: TelegramWebApp) {
  const params = webApp.themeParams ?? {};
  const root = document.documentElement;
  if (params.bg_color) root.style.setProperty("--background", params.bg_color);
  if (params.text_color) root.style.setProperty("--foreground", params.text_color);
  if (params.hint_color) root.style.setProperty("--muted", params.hint_color);
  if (params.secondary_bg_color) root.style.setProperty("--card-bg", params.secondary_bg_color);
  webApp.setHeaderColor?.(params.bg_color ?? "bg_color");
  webApp.setBackgroundColor?.(params.bg_color ?? "bg_color");
}

export default function TgWebAppInit() {
  useEffect(() => {
    const webApp = (window as unknown as { Telegram?: { WebApp?: TelegramWebApp } })
      .Telegram?.WebApp;
    if (!webApp) return;
    webApp.ready();
    webApp.expand();
    applyTheme(webApp);
  }, []);

  return null;
}
