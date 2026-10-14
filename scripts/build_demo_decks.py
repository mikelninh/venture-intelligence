from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'backend' / 'demo'
OUT.mkdir(exist_ok=True)

DECKS = {
 'heliogrid': [
  ('THE OPPORTUNITY', [
   'Company: HelioGrid AI',
   'Tagline: Making industrial power grids more flexible with predictive optimisation.',
   'Sector: Climate Tech / Industrial AI',
   'Headquarters: Berlin, Germany',
   'Founded: 2024',
   'Stage: Seed',
   'Funding sought: EUR 2.4 million',
   'Problem: Factories waste capacity and face high peak-load charges because grid operations are reactive.',
   'Solution: Predictive control software forecasts loads and recommends flexible dispatch before peak events.',
  ]),
  ('HOW WE WORK', [
   'Product: An API-first monitoring and optimisation platform integrated with industrial energy meters.',
   'Traction: 11 pilots, 4 paying customers, and EUR 38k monthly recurring revenue (founder-reported).',
   'Business model: Annual SaaS contract with installation fee and usage-based optimisation module.',
   'Market: Founder-estimated EUR 4.1 billion European industrial energy software opportunity.',
   'Competition: Energy management software providers and in-house industrial automation teams.',
  ]),
  ('THE TEAM AND THE ASK', [
   'Team: Dr. Mara Klein (former grid researcher) and Daniel Wu (industrial SaaS engineering lead).',
   'Risks: Long enterprise sales cycles, integration complexity, and unverified customer savings claims.',
   'Use of funds: 45% product development, 35% go-to-market, 20% security and integrations.',
   'Notes: All figures are invented for the synthetic demo; nothing here is investment advice.',
  ])
 ],
 'novasense': [
  ('THE PROMISE', [
   'Company: NovaSense Robotics',
   'Tagline: Low-cost sensing for safer warehouse robots.',
   'Sector: Industrial AI / Robotics',
   'Headquarters: Hamburg, Germany',
   'Founded: 2025',
   'Stage: Pre-seed',
   'Funding sought: EUR 1.6 million',
   'Problem: Small logistics teams cannot afford advanced proximity sensing.',
   'Solution: Retrofit sensor kits for existing warehouse equipment.',
  ]),
  ('THE STORY', [
   'Product: Low-cost sensor kit and fleet monitoring dashboard.',
   'Traction: 8 paid pilot customers in Germany (founder claim).',
   'Business model: Hardware starter kit plus annual fleet software subscription.',
   'Market: Founders estimate a EUR 600m addressable segment.',
   'Competition: Premium industrial lidar and camera solutions.',
  ]),
  ('A CLOSER LOOK', [
   'Traction: 80 paying customers as of September (conflicting founder claim).',
   'Team: Two robotics engineers and one logistics operator.',
   'Risks: Certification timelines and false-positive detection performance.',
   'Use of funds: 50% product certification, 30% pilots, 20% hiring.',
   'Notes: All claims and numbers in this deck are invented. The inconsistent traction figures are intentional.',
  ]),
 ],
 'lumabio': [
  ('THE OPPORTUNITY', [
   'Company: LumaBio Diagnostics',
   'Tagline: Low-cost optical tools for faster lab screening.',
   'Sector: Life Sciences / Diagnostics',
   'Headquarters: Lyon, France',
   'Founded: 2023',
   'Stage: Pre-seed',
   'Funding sought: EUR 1.1 million',
   'Problem: Small laboratories lack affordable high-throughput preliminary screening.',
   'Solution: Compact light-based reader with machine-learning-assisted signal classification.',
  ]),
  ('EARLY EVIDENCE', [
   'Product: Research-use-only benchtop prototype, currently in validation.',
   'Traction: 3 research pilots; no commercial revenue reported.',
   'Market: Founders describe a fragmented European diagnostic instrumentation market.',
   'Team: A biomedical optics researcher and an embedded systems engineer.',
  ]),
  ('OPEN QUESTIONS', [
   'Risks: Regulatory pathway and performance against gold-standard assays have not been established.',
   'Notes: This fictitious deck intentionally omits competitive positioning and use of funds.',
  ]),
 ]
}

def draw_deck(path, pages, slug):
    c = canvas.Canvas(str(path), pagesize=A4)
    W, H = A4
    for page_idx, (heading, lines) in enumerate(pages):
        c.setFillColor(colors.HexColor('#F7F8F5'))
        c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#0D2130'))
        c.rect(0, H-10, W, 10, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#008A7A'))
        c.setFont('Helvetica-Bold', 10)
        c.drawString(48, H - 55, 'VENTURE INTELLIGENCE / SYNTHETIC DEMO')
        c.setFillColor(colors.HexColor('#15293A'))
        c.setFont('Helvetica-Bold', 28)
        c.drawString(48, H - 110, heading)
        y = H - 165
        for line in lines:
            k, val = line.split(':', 1)
            c.setFont('Helvetica-Bold', 11)
            c.setFillColor(colors.HexColor('#0C615A'))
            c.drawString(48, y, k.upper())
            y -= 18
            c.setFont('Helvetica', 11)
            c.setFillColor(colors.HexColor('#283A43'))
            for segment in simpleSplit(val.strip(), 'Helvetica', 11, W - 100):
                c.drawString(48, y, segment)
                y -= 15
            y -= 15
        c.setStrokeColor(colors.HexColor('#CBD4D3'))
        c.line(48, 58, W - 48, 58)
        c.setFont('Helvetica', 8)
        c.setFillColor(colors.HexColor('#687780'))
        c.drawString(48, 42, 'NOT A REAL STARTUP  -  all people, data and claims are fictional')
        c.drawRightString(W - 48, 42, f'{page_idx+1:02d}/{len(pages):02d}')
        c.showPage()
    c.save()

for slug, pages in DECKS.items():
    draw_deck(OUT / f'{slug}.pdf', pages, slug)
    print(OUT / f'{slug}.pdf')
