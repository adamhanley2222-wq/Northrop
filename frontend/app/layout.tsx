import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MD Strategic Review AI",
  description: "Strategic review assistant demo",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
