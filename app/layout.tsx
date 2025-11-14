import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Cannabis Apotheken Finder",
  description: "Finden Sie medizinische Cannabis-Sorten nach Wirkung und Beschwerden",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
