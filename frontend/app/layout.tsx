import "./globals.css";

export const metadata = {
  title: "RemoteCare AI",
  description: "AI-assisted care coordination for underserved communities."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
