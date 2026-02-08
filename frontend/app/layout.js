import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { AuthProviderWrapper } from "./context/AuthProviderWrapper";

const plusJakarta = Plus_Jakarta_Sans({
  variable: "--font-plus-jakarta",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata = {
  title: "MealUp - Fitness & Nutrition",
  description: "Your AI-powered fitness and nutrition companion",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${plusJakarta.variable} antialiased font-sans`}>
        <div className="blob-cont">
          <div className="blob blob-1"></div>
          <div className="blob blob-2"></div>
          <div className="blob blob-3"></div>
        </div>
        <AuthProviderWrapper>{children}</AuthProviderWrapper>
      </body>
    </html>
  );
}
