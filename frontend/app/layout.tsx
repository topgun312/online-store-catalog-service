import type { Metadata } from "next";
import Script from "next/script";
import TgWebAppInit from "@/components/TgWebAppInit";
import "./globals.css";

export const metadata: Metadata = {
  title: "Каталог",
  description: "Каталог товаров",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <body>
        <TgWebAppInit />
        {children}
        <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />
      </body>
    </html>
  );
}
