"""Hyper-tailored email content for every emailable prospect.

Each company has a hand-written `hook` (a specific product + cocktail idea),
an `audience` descriptor, the `brand` name to reference, and the `ask` specifics.
These are merged into the shared "Sips and Sushi" template so every email is
individually tailored while keeping the approved structure, free-participation
emphasis, sushi angle, event date, and logo consistent.

`**bold**` markers are rendered as <strong> in HTML and stripped in plain text.
"""
from __future__ import annotations

import re

import config

# Per-company tailoring keyed by prospect id (from build_data.py slugs).
TAILORING: dict[str, dict[str, str]] = {
    "diageo-north-america": {
        "brand": "Diageo",
        "hook": "I've long admired the range Diageo brings to a back bar, and I'd love to include it in this year's event. I can already picture one of the bartenders shaking a bright **Tanqueray** gin highball or a silky **Don Julio** margarita - exactly the kind of clean, food-friendly drinks that pair beautifully with a night of fresh sushi.",
        "audience": "bartenders, cocktail enthusiasts, and hospitality professionals",
        "ask": "a few bottles from across the portfolio - Tanqueray, Don Julio, or Ketel One - for the bartenders to build signature serves with, plus any branded glassware or activation support you'd like guests to experience",
    },
    "pernod-ricard-usa": {
        "brand": "Pernod Ricard",
        "hook": "I've been a fan of the Pernod Ricard lineup for years, and I'd love to include it this year. I can picture a bartender pulling together a crowd-pleasing **Kahlúa** espresso martini or a crisp **Absolut** highball - approachable, well-made drinks that keep a room happy between bites of sushi.",
        "audience": "cocktail enthusiasts, bartenders, and hospitality professionals",
        "ask": "a few bottles - Absolut, Jameson, or Kahlúa - for the bartenders to work with, plus any co-marketing or branded touches you'd like",
    },
    "brown-forman": {
        "brand": "Brown-Forman",
        "hook": "I've always had a soft spot for the Brown-Forman family, and I'd love to feature it this year. I can already picture a bartender building a proper **Woodford Reserve** old fashioned or a bright **Herradura** margarita - the kind of confident, classic drinks our guests love to sip alongside sushi.",
        "audience": "whiskey lovers, cocktail enthusiasts, and hospitality professionals",
        "ask": "a few bottles - Woodford Reserve, Old Forester, or Herradura - for the bartenders, a tasting moment, and any co-marketing you're up for",
    },
    "campari-america": {
        "brand": "Campari",
        "hook": "I've been a fan of the Campari portfolio for a long time, and I'd love to include it this year. I can already picture a bartender opening the night with a glowing **Aperol** spritz or a classic **Campari** negroni - that bittersweet, aperitivo-hour energy is exactly the right note to set alongside fresh sushi.",
        "audience": "aperitivo lovers, cocktail enthusiasts, and hospitality professionals",
        "ask": "a few bottles - Aperol, Campari, or Espolòn - for an aperitivo activation, branded glassware, or anything else you'd like guests to experience",
    },
    "william-grant-sons": {
        "brand": "William Grant & Sons",
        "hook": "I've long admired what William Grant & Sons brings to a bar, and I'd love to feature it this year. I can picture a bartender building a cool, cucumber-laced **Hendrick's** gin and tonic or a smooth **Monkey Shoulder** sour - playful, well-crafted drinks that pair beautifully with a night of sushi.",
        "audience": "cocktail enthusiasts, bartenders, and hospitality professionals",
        "ask": "a few bottles - Hendrick's, Monkey Shoulder, or Glenfiddich - for the bartenders to work with, plus any experiential touches you'd like to bring",
    },
    "heaven-hill-brands": {
        "brand": "Heaven Hill",
        "hook": "I've been a fan of Heaven Hill for years, and I'd love to include the range this year. I can already picture a bartender stirring up an **Elijah Craig** old fashioned or a crisp **Deep Eddy** highball - honest, delicious drinks that go down easy between pieces of sushi.",
        "audience": "whiskey lovers, cocktail enthusiasts, and hospitality professionals",
        "ask": "a few bottles - Elijah Craig, Larceny, or Lunazul - for the bartenders, plus a tasting moment for guests",
    },
    "sazerac": {
        "brand": "Sazerac",
        "hook": "Judging by how often your bottles turn up on great back bars, you can guess I'm a fan - and I'd love to feature the Sazerac lineup this year. I can already picture a bartender building a proper **Sazerac** with your rye or a **Buffalo Trace** old fashioned, the kind of timeless drink our guests happily sip all night.",
        "audience": "whiskey lovers, cocktail enthusiasts, and hospitality professionals",
        "ask": "a few bottles - Buffalo Trace, Sazerac Rye, or Wheatley - for the bartenders, plus a tasting for guests",
    },
    "mast-jagermeister-us": {
        "brand": "Jägermeister",
        "hook": "I've always thought Jägermeister is more versatile than people give it credit for, and I'd love to feature it this year. I can picture a bartender serving it ice-cold or folding it into a herbal, cold-brew-tinged highball - a fun, high-energy moment that gets a room going between bites of sushi.",
        "audience": "cocktail enthusiasts, nightlife-savvy guests, and hospitality professionals",
        "ask": "a few bottles for the bartenders (and a tap machine if you have one), plus any nightlife activation touches you'd like",
    },
    "stoli-group": {
        "brand": "Stoli Group",
        "hook": "I've been a fan of the Stoli family for a while, and I'd love to include it this year. I can already picture a bartender shaking a clean **Stoli** martini and a zesty Moscow Mule, or pouring a smooth **Cenote** tequila serve - crisp, food-friendly drinks that pair nicely with sushi.",
        "audience": "cocktail enthusiasts, bartenders, and hospitality professionals",
        "ask": "a few bottles - Stoli, elit, or Cenote - for the bartenders, plus any co-marketing you're open to",
    },
    "hotaling-co": {
        "brand": "Hotaling & Co.",
        "hook": "I've long admired the portfolio Hotaling & Co. represents, and I'd love to feature it this year. I can picture a bartender pouring a beautifully balanced **Junipero** gin martini or a delicate **Nikka** Japanese whisky highball - which, fittingly, is a dream pairing with sushi.",
        "audience": "spirits enthusiasts, bartenders, and hospitality professionals",
        "ask": "a portfolio tasting plus a few bottles for the bartenders to build signature serves around",
    },
    "uncle-nearest": {
        "brand": "Uncle Nearest",
        "hook": "I've been a big admirer of Uncle Nearest - both the whiskey and the story behind it - and I'd love to feature it this year. I can already picture a bartender building a rich **Uncle Nearest** old fashioned while sharing a bit of that history, which is exactly the kind of moment our guests remember.",
        "audience": "whiskey lovers, cocktail enthusiasts, and hospitality professionals",
        "ask": "a few bottles for the bartenders, plus any storytelling or sponsorship support you'd like - we'd love to help tell the brand's story",
    },
    "fever-tree-usa": {
        "brand": "Fever-Tree",
        "hook": "I've been a fan of Fever-Tree for years - your tonics are what make a gin and tonic actually sing - and I'd love to feature them this year. I can already picture a dedicated mixer station where bartenders build crisp **Fever-Tree** highballs, which happen to be a perfect, palate-cleansing match for sushi.",
        "audience": "bartenders, cocktail enthusiasts, and hospitality professionals",
        "ask": "a few cases of your tonics and mixers for a mixer station, plus any branded touches you'd like",
    },
    "q-mixers": {
        "brand": "Q Mixers",
        "hook": "I've been a fan of Q Mixers for a while - that extra-spicy ginger beer is a bartender favorite - and I'd love to feature it this year. I can picture Q as the house mixer behind every highball and mule, keeping drinks crisp and bright all night alongside the sushi.",
        "audience": "bartenders, cocktail enthusiasts, and hospitality professionals",
        "ask": "a few cases of tonic, ginger beer, and club soda - ideally as our official mixer partner - plus any branded touches you'd like",
    },
    "monin-americas": {
        "brand": "MONIN",
        "hook": "I've long relied on MONIN behind the bar, and I'd love to feature it this year. I can already picture our bartenders leaning on your syrups and purées to build the signature cocktails of the night - the kind of bright, balanced flavors that play beautifully against fresh sushi.",
        "audience": "bartenders, cocktail enthusiasts, and hospitality professionals",
        "ask": "a selection of syrups and purées for the bartenders, and we'd love to collaborate on a couple of menu cocktails featuring MONIN",
    },
    "libbey": {
        "brand": "Libbey",
        "hook": "I've always believed the right glass makes a cocktail, and Libbey is the name I trust for that - so I'd love to feature you this year. Picture every signature drink and every sushi-side sip arriving in beautiful Libbey glassware; it genuinely elevates how the whole night looks and feels.",
        "audience": "cocktail enthusiasts, bartenders, and hospitality professionals",
        "ask": "event glassware for the bar - coupes, rocks, and highballs - and we'd happily feature Libbey as our glassware partner",
    },
    "true-brands": {
        "brand": "True Brands",
        "hook": "I've come across True Brands gear at some of my favorite bars, and I'd love to feature you this year. I can picture our bartenders working with your barware all night, and a few fun branded accessories as guest giveaways - the kind of little touch people actually take home and remember.",
        "audience": "cocktail enthusiasts, bartenders, and hospitality professionals",
        "ask": "some branded bar tools for the bartenders and a few giveaways for guests",
    },
    "fee-brothers": {
        "brand": "Fee Brothers",
        "hook": "I've had a bottle (or five) of Fee Brothers on my home bar for years, and I'd love to feature you this year. I can already picture a little bitters station where bartenders finish drinks with your aromatic and orange bitters - those small aromatic flourishes are exactly what our guests geek out over.",
        "audience": "bartenders, cocktail enthusiasts, and hospitality professionals",
        "ask": "an assortment of bitters for the bartenders and a bitters station, plus any sampling you'd like",
    },
    "bittermens": {
        "brand": "Bittermens",
        "hook": "I've been a fan of Bittermens for a long time - your Xocolatl Mole bitters live permanently on my bar - and I'd love to feature you this year. I can picture a bartender using them to add real depth to an old fashioned, and maybe walking guests through what a few dashes can do.",
        "audience": "bartenders, serious cocktail enthusiasts, and hospitality professionals",
        "ask": "a range of your bitters and liqueurs for the bartenders, plus a bartender-led education moment for guests",
    },
    "bittercube": {
        "brand": "Bittercube",
        "hook": "I've admired Bittercube's approach for a while, and I'd love to feature you this year. I can picture your bitters elevating the signature cocktails, and even a short guided taste of how each one changes a drink - guests love that kind of hands-on discovery.",
        "audience": "bartenders, cocktail enthusiasts, and hospitality professionals",
        "ask": "a selection of your bitters for the bartenders, plus any education or light consulting you'd like to contribute",
    },
    "scrappys-bitters": {
        "brand": "Scrappy's Bitters",
        "hook": "I've been a fan of Scrappy's for years - your cardamom and lavender bitters are little magic bottles - and I'd love to feature you this year. I can already picture bartenders using them to add unexpected aromatics to the menu, which our guests always find delightful.",
        "audience": "bartenders, cocktail enthusiasts, and hospitality professionals",
        "ask": "an assortment of your bitters for the bartenders and a sampling moment for guests",
    },
    "peychauds": {
        "brand": "Peychaud's",
        "hook": "You can't talk classic cocktails without Peychaud's, and I'd love to feature you this year. I can already picture a bartender building a proper Sazerac with that unmistakable Peychaud's flush of color and anise - a little piece of cocktail history our guests love to sip.",
        "audience": "cocktail enthusiasts, bartenders, and hospitality professionals",
        "ask": "a few bottles for the bartenders and a classic-cocktail moment built around Peychaud's",
    },
    "regans-orange-bitters": {
        "brand": "Regans'",
        "hook": "Regans' No. 6 is the orange bitters I reach for, and I'd love to feature you this year. I can picture bartenders finishing martinis and old fashioneds with a few dashes - that bright citrus lift is exactly the kind of detail our crowd appreciates.",
        "audience": "cocktail enthusiasts, bartenders, and hospitality professionals",
        "ask": "a few bottles for the bartenders to work with across the menu",
    },
    "liber-co": {
        "brand": "Liber & Co.",
        "hook": "I've been a fan of Liber & Co. for a while - your Fiery Ginger and grenadine punch way above their weight - and I'd love to feature you this year. I can picture bartenders building bright, syrup-forward cocktails around them, and we'd love to collaborate on a recipe or two.",
        "audience": "bartenders, cocktail enthusiasts, and hospitality professionals",
        "ask": "a selection of your syrups for the bartenders, and a recipe collaboration for the menu",
    },
    "small-hand-foods": {
        "brand": "Small Hand Foods",
        "hook": "As someone who's made far too many Mai Tais, I have deep respect for Small Hand Foods orgeat - and I'd love to feature you this year. I can already picture a bartender building a proper tiki drink around your orgeat and pineapple gum, the kind of lush, tropical pour that's surprisingly great with sushi.",
        "audience": "bartenders, tiki and cocktail enthusiasts, and hospitality professionals",
        "ask": "a selection of your syrups for the bartenders, plus a little education moment on why they matter",
    },
    "bg-reynolds": {
        "brand": "BG Reynolds",
        "hook": "I've leaned on BG Reynolds for tiki nights for years, and I'd love to feature you this year. I can picture a whole tiki corner where bartenders build Mai Tais and Jungle Birds with your orgeat and falernum - a fun, tropical counterpoint to the sushi.",
        "audience": "tiki lovers, bartenders, and cocktail enthusiasts",
        "ask": "a selection of your tiki syrups for a dedicated tiki activation",
    },
    "liquid-alchemist": {
        "brand": "Liquid Alchemist",
        "hook": "I've been a fan of Liquid Alchemist for a while - your passion fruit and falernum are bartender staples - and I'd love to feature you this year. I can picture bright, tropical cocktails built around them, and we'd love to collaborate on a couple of menu drinks.",
        "audience": "bartenders, cocktail enthusiasts, and hospitality professionals",
        "ask": "a selection of your syrups for the bartenders and a menu collaboration",
    },
    "proof-syrup": {
        "brand": "Proof Syrup",
        "hook": "I've been a fan of Proof Syrup for a while, and I'd love to feature you this year. I can picture bartenders reaching for your syrups all night to keep the signature drinks balanced and bright - and we'd love to give guests a taste.",
        "audience": "bartenders, cocktail enthusiasts, and hospitality professionals",
        "ask": "a selection of your syrups for the bartenders plus a sampling moment for guests",
    },
    "bittermilk": {
        "brand": "Bittermilk",
        "hook": "I've been a fan of Bittermilk for a while - your No. 1 makes a genuinely great old fashioned - and I'd love to feature you this year. I can picture a cocktail station built around your mixers, so guests get a beautifully made drink with almost no fuss.",
        "audience": "cocktail enthusiasts, bartenders, and hospitality professionals",
        "ask": "a few bottles of your mixers for a cocktail station, plus any branded touches you'd like",
    },
    "withco-cocktails": {
        "brand": "WithCo",
        "hook": "I've been a fan of WithCo for a while, and I'd love to feature you this year. I can picture bartenders using your mixers to turn out consistent, delicious cocktails all night - the kind of effortless quality our guests notice.",
        "audience": "cocktail enthusiasts, bartenders, and hospitality professionals",
        "ask": "a few bottles of your mixers for the bar and a sampling moment for guests",
    },
    "owens-craft-mixers": {
        "brand": "Owen's Craft Mixers",
        "hook": "I've been a fan of Owen's for a while - your ginger beer and grapefruit mixers make an easy drink taste special - and I'd love to feature you this year. I can picture Owen's behind a whole run of crisp highballs and palomas, which pair really nicely with sushi.",
        "audience": "cocktail enthusiasts, bartenders, and hospitality professionals",
        "ask": "a few cases of your mixers for the bar as a mixer partner, plus any branded touches",
    },
    "east-imperial": {
        "brand": "East Imperial",
        "hook": "I've been a fan of East Imperial for a while now - your mixers are the kind of thing bartenders genuinely geek out over - and I'd love to feature them this year. I can already picture a bartender building a crisp, Tokyo-style highball around your **Yuzu Tonic**, letting that bright citrus carry a great gin - which, fittingly, is a perfect match for a night of fresh sushi.",
        "audience": "bartenders, cocktail enthusiasts, and hospitality professionals",
        "ask": "a few cases of tonics and ginger beer for the bartenders to build highballs with, plus any branded glassware or bar tools you'd like guests to experience",
    },
    "thomas-henry": {
        "brand": "Thomas Henry",
        "hook": "I've enjoyed Thomas Henry mixers whenever I've come across them, and I'd love to feature you this year. I can picture your tonic and soda water behind a run of clean, European-style highballs - crisp, light, and a lovely match for sushi.",
        "audience": "bartenders, cocktail enthusiasts, and hospitality professionals",
        "ask": "a few cases of your mixers for the bar, plus any branded touches you'd like",
    },
    "liquid-death": {
        "brand": "Liquid Death",
        "hook": "I love what Liquid Death has done with, of all things, water - and I'd love to feature you this year. I can picture your cans as the hydration hero of the night: a bold-looking palate cleanser between cocktails and sushi that guests will absolutely photograph.",
        "audience": "cocktail enthusiasts, younger professionals, and hospitality creatives",
        "ask": "a few cases of still and sparkling water and any branded activation touches you'd like - your packaging does half the work",
    },
    "recess": {
        "brand": "Recess",
        "hook": "I've been a fan of Recess for a while - the vibe and the drinks both - and I'd love to feature you this year. I can picture a calm, colorful zero-proof station pouring your sparkling waters and mood drinks, a refreshing non-alc option that pairs easily with sushi.",
        "audience": "younger professionals, wellness-minded guests, and a growing sober-curious crowd",
        "ask": "a few cases for a dedicated zero-proof station, plus any branded touches you'd like",
    },
    "ghia": {
        "brand": "Ghia",
        "hook": "I've been a fan of Ghia for a while, and I'd love to feature it this year. I can already picture a bartender pouring a bittersweet **Ghia** spritz as an aperitivo-style welcome - a grown-up, alcohol-free option that sets the tone beautifully alongside the first bites of sushi.",
        "audience": "cocktail enthusiasts, aperitivo lovers, and a growing sober-curious crowd",
        "ask": "a few bottles for zero-proof cocktails at the bar, plus any branded touches you'd like",
    },
    "seedlip": {
        "brand": "Seedlip",
        "hook": "I've been a fan of Seedlip since the early days, and I'd love to feature it this year. I can picture a bartender building a crisp, herbal **Seedlip Garden 108** and tonic - a genuinely elegant zero-proof pour that holds its own next to sushi.",
        "audience": "cocktail enthusiasts, hospitality professionals, and a growing sober-curious crowd",
        "ask": "a few bottles for a proper zero-proof menu at the bar",
    },
    "lyres": {
        "brand": "Lyre's",
        "hook": "I've been impressed by how close Lyre's gets to the real thing, and I'd love to feature it this year. I can already picture a bartender building an alcohol-free negroni or espresso martini with your range - so good most guests won't believe there's no alcohol in it.",
        "audience": "cocktail enthusiasts, hospitality professionals, and a growing sober-curious crowd",
        "ask": "a selection of your spirits for a dedicated zero-proof bar",
    },
    "ritual-zero-proof": {
        "brand": "Ritual Zero Proof",
        "hook": "I've been a fan of Ritual Zero Proof for a while, and I'd love to feature it this year. I can picture a bartender building a zero-proof paloma with your tequila alternative or a spirit-free old fashioned - familiar, satisfying drinks that pair easily with sushi.",
        "audience": "cocktail enthusiasts, hospitality professionals, and a growing sober-curious crowd",
        "ask": "a selection of your alternatives for zero-proof cocktails at the bar",
    },
    "monday-gin": {
        "brand": "Monday",
        "hook": "I've been a fan of Monday for a while, and I'd love to feature it this year. I can already picture a bartender pouring a crisp, juniper-forward **Monday** zero-proof gin and tonic - a clean, refreshing option that's lovely with sushi.",
        "audience": "cocktail enthusiasts, wellness-minded guests, and a growing sober-curious crowd",
        "ask": "a few bottles for a zero-proof station at the bar",
    },
    "dhos": {
        "brand": "Dhos",
        "hook": "I've been a fan of Dhos for a while, and I'd love to feature it this year. I can already picture a bartender building a zero-proof Negroni around your **Bittersweet** - that bitter-orange backbone is exactly what makes an alcohol-free drink feel like a real cocktail, and it's a great match for the clean flavors of sushi.",
        "audience": "hospitality professionals, cocktail enthusiasts, and a growing sober-curious crowd",
        "ask": "a few bottles for the bartenders to build a dedicated zero-proof menu, plus any branded touches",
    },
    "aplos": {
        "brand": "Aplós",
        "hook": "I've been a fan of Aplós for a while, and I'd love to feature it this year. I can already picture a bartender building a bright, celebratory spritz around **Aplós Arise** - real complexity from the botanicals, not just another mocktail, and a lovely light pairing with sushi.",
        "audience": "young professionals, hospitality creatives, and a growing sober-curious crowd",
        "ask": "a few bottles for a dedicated zero-proof activation, plus any branded touches",
    },
    "casamara-club": {
        "brand": "Casamara Club",
        "hook": "I've been a fan of Casamara Club for a while - your amaro-inspired sodas are such a smart idea - and I'd love to feature them this year. I can picture them as a sophisticated, low/no-ABV aperitivo alternative, bittersweet and bubbly and perfect with the first courses of sushi.",
        "audience": "aperitivo lovers, cocktail enthusiasts, and a growing sober-curious crowd",
        "ask": "a few cases for an aperitivo-style zero-proof moment, plus any branded touches",
    },
    "curious-elixirs": {
        "brand": "Curious Elixirs",
        "hook": "I've been a fan of Curious Elixirs for a while, and I'd love to feature them this year. I can picture guests sampling your No. 1 - that bittersweet, negroni-leaning pour - as a ready-to-serve zero-proof option that's genuinely delicious with sushi.",
        "audience": "cocktail enthusiasts, hospitality professionals, and a growing sober-curious crowd",
        "ask": "a few bottles for sampling at the zero-proof bar",
    },
    "de-soi": {
        "brand": "De Soi",
        "hook": "I've been a fan of De Soi for a while, and I'd love to feature it this year. I can already picture a bartender pouring a chilled **De Soi** spritz - beautifully aromatic and grown-up, exactly the kind of alcohol-free apéritif that pairs gracefully with sushi.",
        "audience": "cocktail enthusiasts, aperitivo lovers, and a growing sober-curious crowd",
        "ask": "a few bottles for zero-proof cocktails at the bar",
    },
    "tip-top-proper-cocktails": {
        "brand": "Tip Top Proper Cocktails",
        "hook": "I've been genuinely impressed by Tip Top - a legitimately great cocktail out of a tiny can is no small feat - and I'd love to feature you this year. I can picture your old fashioned and margarita as perfect, no-wait pours to keep the room happy between sushi courses.",
        "audience": "cocktail enthusiasts, hospitality professionals, and design-savvy guests",
        "ask": "a few cases for sampling at the bar, plus any branded touches you'd like",
    },
    "social-hour-cocktails": {
        "brand": "Social Hour",
        "hook": "I've been a fan of Social Hour for a while - great drinks and gorgeous cans - and I'd love to feature you this year. I can picture your spritzes and margaritas as easy, elegant pours that keep the night flowing alongside the sushi.",
        "audience": "cocktail enthusiasts, design-savvy guests, and hospitality professionals",
        "ask": "a few cases for sampling at the bar, plus any branded touches",
    },
    "post-meridiem": {
        "brand": "Post Meridiem",
        "hook": "I've been impressed by Post Meridiem - your espresso martini in a can is dangerously good - and I'd love to feature you this year. I can picture them as instant crowd-pleasers between sushi courses when the bar gets busy.",
        "audience": "cocktail enthusiasts, hospitality professionals, and younger professionals",
        "ask": "a few cases for sampling at the bar, plus any branded touches",
    },
    "livewire-drinks": {
        "brand": "LiveWire",
        "hook": "I've been a fan of LiveWire for a while, and I'd love to feature you this year. I can picture your canned cocktails on hand for fast, high-quality pours - and given your bartender-led roots, we'd love to collaborate on a serve with our bartenders.",
        "audience": "cocktail enthusiasts, bartenders, and hospitality professionals",
        "ask": "a few cases for the bar, and a bartender-led collaboration if you're up for it",
    },
    "two-chicks-cocktails": {
        "brand": "Two Chicks",
        "hook": "I've been a fan of Two Chicks for a while, and I'd love to feature you this year. I can picture your light, sessionable cans as an easy, refreshing option that pairs nicely with sushi and keeps the night going.",
        "audience": "cocktail enthusiasts, younger professionals, and hospitality professionals",
        "ask": "a few cases for sampling at the bar, plus any branded touches",
    },
    "onda": {
        "brand": "Onda",
        "hook": "I've been a fan of Onda for a while, and I'd love to feature it this year. I can picture your tequila seltzers as a crisp, easy-drinking option - bright and citrusy, and honestly a great light match for sushi.",
        "audience": "cocktail enthusiasts, younger professionals, and hospitality professionals",
        "ask": "a few cases for sampling at the bar, plus any branded touches",
    },
    "volley-tequila-seltzer": {
        "brand": "Volley",
        "hook": "I've been a fan of Volley for a while - real tequila, real juice, nothing weird - and I'd love to feature it this year. I can picture your seltzers as a clean, refreshing pour that pairs beautifully with the lighter notes of sushi.",
        "audience": "cocktail enthusiasts, wellness-minded guests, and younger professionals",
        "ask": "a few cases for sampling at the bar, plus any branded touches",
    },
    "loverboy": {
        "brand": "Loverboy",
        "hook": "I've been a fan of Loverboy for a while, and I'd love to feature it this year. I can picture your sparkling hard teas and spritzes as a fun, sessionable option that keeps the energy up between sushi courses.",
        "audience": "younger professionals, cocktail enthusiasts, and hospitality creatives",
        "ask": "a few cases for sampling at the bar, plus any branded touches",
    },
    "juneshine": {
        "brand": "JuneShine",
        "hook": "I've been a fan of JuneShine for a while, and I'd love to feature it this year. I can picture your hard kombucha and canned cocktails as a lighter, better-for-you option - crisp and tangy, and a nice foil to richer bites of sushi.",
        "audience": "wellness-minded guests, younger professionals, and cocktail enthusiasts",
        "ask": "a few cases for sampling at the bar, plus any branded touches",
    },
    "haus": {
        "brand": "Haus",
        "hook": "I've been a fan of Haus for a while, and I'd love to feature it this year. I can already picture a bartender pouring a low-ABV **Haus** spritz as an aperitivo-hour welcome - light, bittersweet, and lovely with the first bites of sushi.",
        "audience": "aperitivo lovers, cocktail enthusiasts, and hospitality professionals",
        "ask": "a few bottles for an aperitif activation at the bar, plus any branded touches",
    },
    "italicus": {
        "brand": "Italicus",
        "hook": "I've been a fan of Italicus for a while, and I'd love to feature it this year. I can already picture a bartender opening the evening with an **Italicus Rosolio di Bergamotto** spritz - that bergamot-and-chamomile lift over prosecco sets a beautiful aperitivo tone, and it plays gorgeously against fresh sushi.",
        "audience": "spirits enthusiasts, aperitivo lovers, and hospitality professionals",
        "ask": "a few bottles for an aperitivo activation, branded glassware, or anything else you'd like guests to experience",
    },
    "giffard-usa": {
        "brand": "Giffard",
        "hook": "I've relied on Giffard behind the bar for years, and I'd love to feature you this year. I can picture bartenders building bright, layered cocktails with your liqueurs - and a little tasting of the range for guests who love to learn what goes into a great drink.",
        "audience": "bartenders, cocktail enthusiasts, and hospitality professionals",
        "ask": "a selection of your liqueurs and syrups for the bartenders, plus a tasting and education moment",
    },
    "luxardo": {
        "brand": "Luxardo",
        "hook": "I've had a jar of Luxardo cherries and a bottle of your Maraschino on my bar forever, and I'd love to feature you this year. I can picture bartenders building an Aviation or Last Word with your Maraschino and finishing manhattans with those iconic cherries - the details our guests notice and love.",
        "audience": "cocktail enthusiasts, bartenders, and hospitality professionals",
        "ask": "a selection of your liqueurs and cherries for the bartenders, plus a little education moment",
    },
    "tempus-fugit-spirits": {
        "brand": "Tempus Fugit",
        "hook": "I'm a bit of a cocktail-history nerd, so Tempus Fugit is a personal favorite - and I'd love to feature you this year. I can picture a bartender building a Gran Classico negroni or a historically-minded serve with your Crème de Cacao, and sharing the story behind these recreations with guests.",
        "audience": "serious cocktail enthusiasts, bartenders, and hospitality professionals",
        "ask": "a selection of your spirits for the bartenders, plus an education moment on the history behind them",
    },
    "pierre-ferrand-maison-ferrand": {
        "brand": "Maison Ferrand",
        "hook": "I've long admired the Maison Ferrand portfolio, and I'd love to feature it this year. I can picture a bartender building a silky Ferrand Cognac sidecar, a bright Planteray rum daiquiri, or a margarita lifted by your Dry Curaçao - a genuinely versatile lineup for a night of sushi and cocktails.",
        "audience": "spirits enthusiasts, bartenders, and hospitality professionals",
        "ask": "a portfolio tasting plus a few bottles for the bartenders to build signature serves around",
    },
    "laird-company": {
        "brand": "Laird & Company",
        "hook": "As America's oldest distiller, Laird's has a story I love telling, and I'd love to feature you this year. I can already picture a bartender building a classic Jack Rose with your Applejack - a bit of living cocktail history that our guests really enjoy discovering.",
        "audience": "whiskey and heritage-spirit lovers, cocktail enthusiasts, and hospitality professionals",
        "ask": "a few bottles for the bartenders and a heritage-cocktail moment built around Laird's",
    },
    "novo-fogo": {
        "brand": "Novo Fogo",
        "hook": "I've been a fan of Novo Fogo for a while - great cachaça and a genuinely inspiring sustainability story - and I'd love to feature you this year. I can already picture a bartender building a bright, limey caipirinha with your cachaça, a zesty pour that's lovely alongside sushi.",
        "audience": "cocktail enthusiasts, sustainability-minded guests, and hospitality professionals",
        "ask": "a few bottles for the bartenders, and we'd love to help share your sustainability story with guests",
    },
    "avua-cachaca": {
        "brand": "Avuá",
        "hook": "I've been a fan of Avuá for a while - your Amburana in particular is stunning - and I'd love to feature you this year. I can picture a bartender building a caipirinha with your Prata or a spiced, barrel-aged sip with the Amburana, and walking guests through what makes cachaça special.",
        "audience": "cocktail enthusiasts, bartenders, and hospitality professionals",
        "ask": "a few bottles for the bartenders, plus a little education moment on cachaça",
    },
    "hamilton-rum": {
        "brand": "Hamilton Rum",
        "hook": "I've been a fan of Hamilton Rum for a while - your rums are a bit of a bartender's secret weapon - and I'd love to feature them this year. I can already picture a bartender building a proper Mai Tai or Jungle Bird around your **Jamaican Pot Still Black**, and a well-balanced tiki drink is a surprisingly fun counterpoint to a plate of sushi.",
        "audience": "craft cocktail enthusiasts, tiki lovers, and working bartenders",
        "ask": "a few bottles across the range for the bartenders, a little tiki/craft education, or anything else you'd like guests to experience",
    },
    "appleton-estate": {
        "brand": "Appleton Estate",
        "hook": "I've been a fan of Appleton Estate for a while, and I'd love to feature it this year. I can already picture a bartender building a rich rum old fashioned or a proper Jamaican rum punch with your aged expressions, and sharing a bit about what makes Appleton so distinctive.",
        "audience": "rum lovers, cocktail enthusiasts, and hospitality professionals",
        "ask": "a few bottles for the bartenders and a rum education moment for guests",
    },
    "mijenta-tequila": {
        "brand": "Mijenta",
        "hook": "I've been a fan of Mijenta for a while - beautiful tequila and a real commitment to sustainability - and I'd love to feature it this year. I can already picture a bartender building a fresh **Mijenta** blanco margarita or serving it neat to sip, which is a lovely match for sushi.",
        "audience": "tequila lovers, cocktail enthusiasts, and sustainability-minded guests",
        "ask": "a few bottles for the bartenders, and we'd love to highlight your sustainability story",
    },
    "codigo-1530": {
        "brand": "Código 1530",
        "hook": "I've been a fan of Código 1530 for a while, and I'd love to feature it this year. I can already picture a bartender building a crisp **Código** blanco margarita or pouring the Rosa for something a little special - premium, food-friendly sips that pair beautifully with sushi.",
        "audience": "tequila lovers, cocktail enthusiasts, and hospitality professionals",
        "ask": "a few bottles for the bartenders and a premium tequila activation at the bar",
    },
}


def _fallback(prospect: dict) -> dict:
    brand = (prospect.get("brands", "").split(";")[0].strip()
             or prospect.get("company", "your brand"))
    return {
        "brand": prospect.get("company", brand),
        "hook": (f"I've been an admirer of {prospect.get('company', 'your brand')} for a "
                 f"while, and I'd love to feature it this year. I can already picture one "
                 f"of the bartenders building a signature cocktail around **{brand}** - "
                 f"the kind of well-made drink that pairs beautifully with fresh sushi."),
        "audience": "cocktail enthusiasts, bartenders, and hospitality professionals",
        "ask": ("a few bottles for the bartenders to work with, plus any branded touches "
                "you'd like guests to experience"),
    }


def _short_date() -> str:
    # "August 22, 2026" -> "Aug 22"
    d = config.EVENT.get("date", "")
    m = re.match(r"([A-Za-z]+)\s+(\d+)", d)
    if m:
        return f"{m.group(1)[:3]} {m.group(2)}"
    return d


def build_subject(prospect: dict) -> str:
    return f"Inviting {prospect['company']} to {config.EVENT['name']} ({_short_date()}, NYC)"


def _raw_body(prospect: dict) -> str:
    tail = TAILORING.get(prospect["id"]) or _fallback(prospect)
    org = config.ORGANIZER
    ev = config.EVENT
    return f"""Hi {prospect['company']} team,

I hope you're doing well!

My name is {org['name']}, and I'm one of the organizers of **{ev['name']}**, a cocktail showcase we're hosting in New York on **{ev['date']}** featuring a group of incredibly talented up-and-coming bartenders - paired, as the name suggests, with fresh, chef-prepared sushi all evening.

This year will be the **fifth edition** of the showcase, and it's become one of our favorite events to put together. We'll have more than 100 guests spending the evening tasting original cocktails, pairing them with the sushi, meeting the bartenders behind the drinks, and discovering the products that make them special.

{tail['hook']}

The audience is made up of **{tail['audience']}**, so it's a group that genuinely appreciates discovering well-made products rather than simply trying another drink.

We're already lining up a handful of well-known spirits brands for this year's showcase, and we'd love to have **{tail['brand']}** alongside them.

Just to be clear, taking part is completely free - there's no sponsorship fee of any kind, only whatever product or support you're comfortable providing. If you'd be interested, we'd be glad to feature whatever makes the most sense from your perspective - {tail['ask']}.

If you'd like, I'd be happy to send over a little more about the event, the bartenders, and what we have planned.

Thanks so much for taking the time to read this. We'd love the opportunity to introduce **{tail['brand']}** to our guests and hopefully create a few new fans along the way.

Cheers,

{org['name']}
{config.REPLY_TO}"""


def to_text(prospect: dict) -> str:
    return _raw_body(prospect).replace("**", "")


def to_html(prospect: dict, logo_cid: str | None = None) -> str:
    raw = _raw_body(prospect)
    paragraphs = []
    for block in raw.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        block = block.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        block = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", block)
        block = block.replace("\n", "<br>")
        paragraphs.append(f'<p style="margin:0 0 16px;">{block}</p>')
    inner = "\n".join(paragraphs)
    logo_html = (
        f'<div style="text-align:center;margin-bottom:18px;">'
        f'<img src="cid:{logo_cid}" alt="Sips and Sushi" '
        f'style="max-width:220px;height:auto;" /></div>'
        if logo_cid else ""
    )
    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:24px;background:#f4f4f5;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;
              padding:28px 32px;font-family:Helvetica,Arial,sans-serif;
              color:#1f2933;font-size:15px;line-height:1.6;">
    {logo_html}
    {inner}
  </div>
</body></html>"""
