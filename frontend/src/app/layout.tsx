import type { Metadata, Viewport } from "next";
import "./globals.css";
import "./readability.css";
import Pwa from "@/components/pwa";

export const metadata: Metadata = {
  title: "Nexora AI · A little less admin. A lot more teaching.",
  description:
    "A calmer school day. Attendance, assignments and thoughtful AI learning tools in one place.",
  manifest: "/manifest.webmanifest",
  icons: { icon: "/icon.svg", apple: "/icon-192.png" },
};
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#247454",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Pwa />
        {children}
      </body>
    </html>
  );
}
