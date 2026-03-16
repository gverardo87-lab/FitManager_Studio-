import type { Metadata } from "next";
import { Inter, Caveat } from "next/font/google";
import { Providers } from "@/lib/providers";
import { TooltipProvider } from "@/components/ui/tooltip";
import "./globals.css";
import "../styles/product-recipes.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-geist-sans",
  display: "swap",
});

const caveat = Caveat({
  subsets: ["latin"],
  variable: "--font-caveat",
  display: "swap",
});

export const metadata: Metadata = {
  title: "FitManager Studio+",
  description: "CRM gestionale per personal trainer - privacy first, zero cloud.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="it">
      <body className={`antialiased ${inter.variable} ${caveat.variable}`}>
        <Providers>
          <TooltipProvider>{children}</TooltipProvider>
        </Providers>
      </body>
    </html>
  );
}
