import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "saengibu-portal",
  description: "학교생활기록부 포털",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
