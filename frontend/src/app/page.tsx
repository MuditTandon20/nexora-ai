import Link from "next/link";
import { ArrowUpRight, BookOpen, Check, Leaf, Sparkles } from "lucide-react";

export default function Home() {
  return (
    <div className="landing">
      <nav className="landing-nav">
        <Link href="/" className="brand">
          <span className="brand-icon">
            N<span>✦</span>
          </span>
          nexora<span className="ai-tag">AI</span>
        </Link>
        <Link className="button secondary" href="/login">
          School sign in <ArrowUpRight size={16} />
        </Link>
      </nav>
      <main>
        <div className="landing-hero">
          <div>
            <span className="eyebrow">
              <Leaf size={15} /> A LITTLE SPACE TO GROW
            </span>
            <h1>
              Less admin.
              <br />
              More <em>aha!</em>
              <br />
              moments.
            </h1>
            <p>
              Your school day, a little lighter. One thoughtful workspace for
              teaching, learning, and everything in between.
            </p>
            <Link href="/login" className="button">
              Enter your school <ArrowUpRight size={18} />
            </Link>
            <div className="hero-note">
              <Check size={16} /> Built for teachers. Made for curious minds.
            </div>
          </div>
          <div className="hero-art">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="art-card art-back">
              <BookOpen size={32} />
              <span>A world of possibility</span>
              <strong>
                One classroom
                <br />
                at a time.
              </strong>
              <div className="abstract-plant">✳</div>
            </div>
            <div className="art-card art-front">
              <span className="icon-tile">
                <Check size={22} />
              </span>
              <div>
                <strong>Attendance? Done.</strong>
                <p>More time for what matters.</p>
              </div>
            </div>
            <div className="art-spark">
              <Sparkles size={24} />
            </div>
            <span className="art-caption">
              SMALL TOOLS. MEANINGFUL DIFFERENCE.
            </span>
          </div>
        </div>
        <div className="landing-features">
          {[
            [
              "01",
              "A calmer classroom",
              "Attendance, notes and homework, beautifully together.",
            ],
            [
              "02",
              "A thoughtful AI companion",
              "Chapter-based practice and explanations, with teachers in control.",
            ],
            [
              "03",
              "Room for curiosity",
              "Little learning challenges that celebrate progress.",
            ],
          ].map(([n, t, d]) => (
            <article key={n}>
              <span>{n}</span>
              <h3>{t}</h3>
              <p>{d}</p>
            </article>
          ))}
        </div>
      </main>
      <footer>
        NEXORA AI <span>Less Admin. More Teaching. Better Learning.</span>
        <span>Made for school days.</span>
      </footer>
    </div>
  );
}
