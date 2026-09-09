"""The seller prep list itself. One source of truth for every word on the page.

Voice: second person to the seller, never a corporate "we". The page is shared
across realtors, so no sentence may assume who is handing it over. Where the
realtor speaks, the build substitutes them from agents.json. That is the
realtor-agnostic rule made mechanical rather than remembered.

Copy rules that bind here (fieldwork CLAUDE.md, locked 2026-08-16):
  - The homeowner test. If a seller would have to ask what a term means it does
    not ship. Where their own paperwork uses a trade word (chattels, fixtures,
    discharge) the word is named AND explained, because they will read it on a
    document either way.
  - No em-dashes, no en-dashes, never the word "AI", no finance jargon.
  - Answer first, workings in folds, state the next step.

Every factual claim carries a source in SOURCES below and a `src` key on the
item. A claim with no source does not go on the page: this is handed to sellers
who will act on it, and a wrong number costs them real money.

FLAGS control who sees an item:
  condo       only when the seller says the home is a condo
  freehold    only when it is not a condo
  buying      only when the seller is buying another home at the same time
  rented_kit  only when the home has rented equipment (water heater and such)
"""

BRAND = {
    "brokerage": "THE AGENCY",
    "red": "#ED2127",
}

# ---------------------------------------------------------------------------
# Sources. Every one was read during the build; the page links the ones a
# seller would actually want to open.
# ---------------------------------------------------------------------------
SOURCES = {
    "serviceontario": (
        "ServiceOntario, change my address",
        "https://www.ontario.ca/page/change-my-address-ontario-services"),
    "canadapost": (
        "Canada Post, mail forwarding",
        "https://www.canadapost-postescanada.ca/cpc/en/personal/mail-forwarding.page"),
    "cra_principal": (
        "Canada Revenue Agency, reporting the sale of your principal residence",
        "https://www.canada.ca/en/revenue-agency/programs/about-canada-revenue-agency-cra"
        "/federal-government-budgets/budget-2016-growing-middle-class"
        "/reporting-sale-your-principal-residence-individuals.html"),
    "cra_tips": (
        "Canada Revenue Agency, report the sale of your principal residence",
        "https://www.canada.ca/en/revenue-agency/news/newsroom/tax-tips"
        "/tax-filing-season-media-kit/tfsmk27.html"),
    "discharge": (
        "Mortgage discharge in Ontario, how it works and what it costs",
        "https://ownright.com/blog/home-finance/mortgage-discharge-in-ontario-how-it-works-and-costs"),
    "porting": (
        "Mortgage porting in Ontario",
        "https://ownright.com/blog/buying-real-estate/mortgage-porting-in-ontario-take-your-rate-with-you"),
    "rentals": (
        "What to know about rented water heaters and other rented equipment",
        "https://www.deeded.ca/blog/what-homebuyers-need-to-know-about-rental-water-heaters-and-other-rental-items"),
    "rentals_clause": (
        "The rented equipment clause in the Agreement of Purchase and Sale",
        "https://ontariorealestatesource.com/rental-items-clause-in-the-agreement-of-purchase-and-sale/"),
    "chattels": (
        "What is included when you buy a home in Ontario",
        "https://harveykalles.com/blog/what-is-included-when-you-buy-a-home-an-ontario-buyers-guide-to-chattels-and-fixtures"),
    "insurance": (
        "Property insurance and real estate closings",
        "https://www.kormans.ca/blog/property-insurance-and-real-estate-closings"),
    "condo_move": (
        "Booking a condo elevator for a move",
        "https://aleksmoving.ca/condo-elevator-booking/"),
    "ldc": (
        "Ontario local hydro utilities, find yours",
        "https://energyrates.ca/ontario/ontarios-local-hydro-utilities-ldc/"),
}

# ---------------------------------------------------------------------------
# The three things that go wrong. Surface, before any list.
# ---------------------------------------------------------------------------
HEADLINES = [
    {
        "n": "01",
        "title": "Keep the house insured until your lawyer says it closed",
        "body": "Not until closing day. Until your lawyer confirms the deal "
                "registered. Closings often slip by a day, and an uninsured day "
                "could haunt you.",
    },
    {
        "n": "02",
        "title": "Ask your lender for the payout figure the day the deal is firm",
        "body": "Ending a mortgage early carries a penalty, and on a fixed rate "
                "it is usually the biggest single cost of selling. Get that number "
                "in writing now, while you can still do something about it.",
    },
    {
        "n": "03",
        "title": "Book the movers before you do anything else on this page",
        "body": "Most deals close on the last day of the month, so every seller "
                "wants the same truck on the same morning. In a condo the elevator "
                "books out too.",
    },
]

# ---------------------------------------------------------------------------
# The phases. `offset` is days before closing; the page turns it into a real
# date the moment a seller has one.
# ---------------------------------------------------------------------------
PHASES = [
    {
        "key": "firm",
        "offset": None,
        "label": "As soon as the sale is firm",
        "lede": "Five calls in the first week. Everything after this is easier "
                "if these five happen now.",
        "items": [
            {
                "id": "lawyer",
                "title": "Send the signed agreement to your lawyer",
                "detail": "If you do not have a real estate lawyer yet, get one "
                          "this week. Send the whole agreement, including every "
                          "page you both signed after it, not just the front one. "
                          "Your lawyer puts the house into the buyer's name, pays "
                          "off your mortgage and handles the money. None of that "
                          "starts until they have the paperwork.",
            },
            {
                "id": "lender",
                "title": "Tell your lender you are selling, and ask for the payout statement",
                "detail": "Ask for three numbers in writing: what you still "
                          "owe, the fee to close the mortgage, and the penalty for "
                          "paying it off early. On a fixed rate that penalty is "
                          "worked out one of two ways and one of them is far "
                          "bigger, so ask for the real number, not an estimate. If "
                          "you are buying again, ask on the same call whether your "
                          "mortgage can move to the new home at the same rate, and "
                          "how many days the lender allows between the two sales.",
                "src": ["discharge", "porting"],
                "money": True,
            },
            {
                "id": "movers",
                "title": "Book the movers",
                "detail": "Get the quote in writing: the date, the start time, "
                          "both addresses, the price, and what their insurance pays "
                          "if they break something of yours. The end of the month "
                          "fills up first, because that is when most sales close.",
            },
            {
                "id": "condo-rules",
                "title": "Ask the building for its moving rules, and book the elevator",
                "detail": "Buildings set the hours, the entrance, and how much "
                          "notice they need, which runs from about a week to a "
                          "month. Most also want a deposit you get back if nothing "
                          "is damaged, plus proof your mover is insured with the "
                          "building's name on it. Ask the mover for that proof when "
                          "you book, not on the morning. Turned away at eight "
                          "o'clock and you have lost the elevator for the day.",
                "flags": ["condo"],
                "src": ["condo_move"],
            },
            {
                "id": "insurance-tell",
                "title": "Tell your insurer the closing date, and do not cancel anything",
                "detail": "The house is yours until it legally changes hands, "
                          "whatever the calendar says. Give your insurer the closing "
                          "date so the policy runs past it, and do not cancel "
                          "anything until your lawyer says the deal is done.",
                "src": ["insurance"],
                "critical": True,
            },
            {
                "id": "chattels",
                "title": "Reread what you agreed to leave behind",
                "detail": "The rule is simple. Anything bolted, wired or "
                          "plumbed in stays with the house, unless the agreement "
                          "says in writing that you are taking it. Anything loose "
                          "goes with you, unless the agreement says in writing that "
                          "it stays. So check the light you meant to keep, the "
                          "shed, the television on the wall, the appliances. Do it "
                          "now, while there is still time to talk about it, rather "
                          "than on the morning when it turns into an argument.",
                "src": ["chattels"],
            },
        ],
    },
    {
        "key": "d60",
        "offset": 60,
        "label": "About two months out",
        "lede": "The paperwork that takes other people time. Start it before you "
                "start packing.",
        "items": [
            {
                "id": "rentals",
                "title": "Find every rental contract and decide: pay it out, or hand it over",
                "detail": "Water heater, furnace, air conditioner, water "
                          "softener, air exchanger, alarm gear. These companies "
                          "usually put a claim on the house, so your lawyer has to "
                          "clear it either way. Either the buyer agrees to take the "
                          "contract over, which has to be written into the "
                          "agreement, or you pay it off before closing. Ask each "
                          "company what the payoff is now. It gets smaller as the "
                          "equipment ages, and it is not a number you want to meet "
                          "for the first time on closing day.",
                "flags": ["rented_kit"],
                "src": ["rentals", "rentals_clause"],
                "money": True,
            },
            {
                "id": "lawyer-docs",
                "title": "Send your lawyer the rest of what they asked for",
                "detail": "Usually: photo identification for everyone whose "
                          "name is on the house, your mortgage details, any rental "
                          "contracts, the property survey if you have one, and "
                          "where to send your mail. If any of those names has "
                          "changed since you bought, through marriage, separation "
                          "or a death, say so now. It adds steps.",
            },
            {
                "id": "status",
                "title": "Get the status certificate ordered if the buyer has not",
                "detail": "It is the building's official information package, "
                          "and the buyer's side usually orders it. It comes from "
                          "your building though, and it carries the moving rules "
                          "you need anyway. Ask management how long they take.",
                "flags": ["condo"],
            },
            {
                "id": "repairs",
                "title": "Book anything you agreed to fix",
                "detail": "If the deal included repairs, get them done and keep the "
                          "invoices. The buyer walks through before closing and "
                          "will look for exactly these.",
            },
            {
                "id": "two-closings",
                "title": "Line your two closing dates up with your lawyer",
                "detail": "Selling and buying on the same day is normal, and it "
                          "is tight. The money from your sale usually pays for your "
                          "purchase, and it does not move until the afternoon. If "
                          "the two dates do not line up, you need a short loan to "
                          "cover the gap, arranged well before the day.",
                "flags": ["buying"],
            },
            {
                "id": "declutter",
                "title": "Start giving things away",
                "detail": "Movers charge by weight or by hour. Everything you do "
                          "not take is money you do not spend, and this is the "
                          "part that always takes longer than people expect.",
            },
        ],
    },
    {
        "key": "d30",
        "offset": 30,
        "label": "One month out",
        "lede": "Address changes and utilities. Mail forwarding takes a week and "
                "a half to switch on, so it starts here.",
        "items": [
            {
                "id": "mail",
                "title": "Set up mail forwarding",
                "detail": "Canada Post takes five to ten business days to start, so "
                          "buying it now means it is live on the day you leave. You "
                          "can forward for one person or for everyone at the "
                          "address, and you can extend it later. Treat it as a "
                          "safety net rather than the plan: it catches what you "
                          "forget to change.",
                "src": ["canadapost"],
                "link": ("Set up forwarding at Canada Post",
                         "https://www.canadapost-postescanada.ca/cpc/en/personal/mail-forwarding.page"),
            },
            {
                "id": "serviceontario",
                "title": "Update your driver's licence, plates and health card",
                "detail": "You get six days after you move to update your "
                          "driver's licence and vehicle permit. That is the law, "
                          "and it is easy to miss. One session online covers the "
                          "licence, the plates, the health card and the photo card "
                          "in one go.",
                "src": ["serviceontario"],
                "link": ("Change your address with ServiceOntario",
                         "https://www.ontario.ca/page/change-my-address-ontario-services"),
                "critical": True,
            },
            {
                "id": "utilities",
                "title": "Book the final readings for the day of closing, not before",
                "detail": "Electricity, gas, water, internet, telephone. Give "
                          "each one the closing date as your last day. Do not shut "
                          "anything off early: the buyer walks through the house "
                          "just before closing and needs the lights and the heat "
                          "working. Which electricity company you are with depends "
                          "on where you live, so check the name on a bill if you "
                          "are not sure.",
                "src": ["ldc"],
                "link": ("Find your electricity company",
                         "https://energyrates.ca/ontario/ontarios-local-hydro-utilities-ldc/"),
                "critical": True,
            },
            {
                "id": "services",
                "title": "Cancel or move the services that come to the house",
                "detail": "Alarm monitoring, lawn care, snow clearing, pool service, "
                          "pest control, cleaners, water delivery, propane. Some "
                          "will move with you and some will not, and most want "
                          "notice.",
            },
            {
                "id": "address-list",
                "title": "Work through the address list",
                "detail": "Bank and credit cards, employer and payroll, the Canada "
                          "Revenue Agency, your pension and investment accounts, "
                          "car and life insurance, the schools, your doctor, "
                          "dentist, pharmacy and veterinarian, any subscription "
                          "that arrives in a box, and the gym. The tax one matters "
                          "more than it looks: a refund or a benefit cheque sent to "
                          "an old address is slow to untangle.",
                "list": [
                    "Bank, credit cards, loans",
                    "Employer and payroll",
                    "Canada Revenue Agency",
                    "Pension and investments",
                    "Car and life insurance",
                    "Schools and daycare",
                    "Doctor, dentist, pharmacy",
                    "Veterinarian",
                    "Subscriptions and deliveries",
                    "Gym and memberships",
                ],
            },
            {
                "id": "records",
                "title": "Ask for your records if you are leaving the area",
                "detail": "Medical, dental and veterinary files, and the children's "
                          "school records. Easier to request while you are still a "
                          "current patient.",
            },
            {
                "id": "eat-down",
                "title": "Start eating the freezer",
                "detail": "Frozen and tinned food is heavy, and most movers will "
                          "not take anything that can leak or thaw.",
            },
        ],
    },
    {
        "key": "d14",
        "offset": 14,
        "label": "Two weeks out",
        "lede": "Confirm what you booked, and start gathering what the buyer needs "
                "on the other side.",
        "items": [
            {
                "id": "confirm-movers",
                "title": "Confirm the movers in writing",
                "detail": "Date, arrival time, both addresses, the price and what "
                          "happens if the closing moves by a day. Ask what they "
                          "will not carry: paint, propane, cleaning chemicals and "
                          "anything that burns are usually refused.",
            },
            {
                "id": "confirm-elevator",
                "title": "Confirm the elevator, and send the building your mover's insurance",
                "detail": "Call the office rather than assuming the booking "
                          "held. Send the mover's proof of insurance now, so "
                          "somebody has time to read it before the day.",
                "flags": ["condo"],
            },
            {
                "id": "keys",
                "title": "Gather every key, remote and code in the house",
                "detail": "Front, back, side, garage, shed, gate, mailbox, storage "
                          "locker, window locks, the pool gate. Garage remotes and "
                          "the keypad code. The alarm code and the monitoring "
                          "company's password. Anything you hold that the buyer "
                          "will need, including the copies at your neighbour's and "
                          "your mother's.",
            },
            {
                "id": "kids-pets",
                "title": "Arrange somewhere for the children and the pets to be",
                "detail": "Moving day is doors propped open, strangers carrying "
                          "heavy things, and nobody watching the driveway.",
            },
            {
                "id": "first-night",
                "title": "Pack the first night box and keep it with you",
                "detail": "Bedding, towels, toilet paper, soap, phone chargers, "
                          "medication, coffee and something to make it in, a change "
                          "of clothes, basic tools, and the paperwork for the "
                          "closing. This box travels in your car, never in the truck.",
            },
        ],
    },
    {
        "key": "d7",
        "offset": 7,
        "label": "The last week",
        "lede": "Signing, and the last of the loose ends.",
        "items": [
            {
                "id": "sign",
                "title": "Sign at your lawyer's office",
                "detail": "This usually happens a few days before closing, not "
                          "on the day. Bring photo identification for everyone "
                          "whose name is on the house. While you are there, settle "
                          "exactly where your money goes and how it reaches you.",
            },
            {
                "id": "returns",
                "title": "Give back anything that is not yours",
                "detail": "Cable boxes, modems, alarm panels, propane tanks, "
                          "water cooler bottles, library books. Anything you keep "
                          "gets billed to you months later, at a price nobody would "
                          "have agreed to up front.",
            },
            {
                "id": "parking",
                "title": "Sort out where the truck parks",
                "detail": "On a narrow street or downtown you may need a permit "
                          "from the city, and it takes a few days. In a condo the "
                          "loading dock is booked with the elevator.",
            },
            {
                "id": "fuel",
                "title": "Top up the oil or propane if the agreement says so",
                "detail": "Fuel in a tank is usually settled between the two sides "
                          "at closing. Get the fill done and give your lawyer the "
                          "receipt.",
                "flags": ["freehold"],
            },
        ],
    },
    {
        "key": "moving",
        "offset": 1,
        "label": "Moving day",
        "lede": "The house has to be empty, clean, and holding everything you "
                "agreed to leave.",
        "items": [
            {
                "id": "meters",
                "title": "Photograph every meter",
                "detail": "Electricity, gas, water. Make sure the numbers are "
                          "readable and the date is on the photo. This is the only "
                          "thing standing between you and a final bill that covers "
                          "somebody else's use.",
                "critical": True,
            },
            {
                "id": "sweep",
                "title": "Walk the house yourself, opening everything",
                "detail": "Every cupboard and closet, the medicine cabinet, behind "
                          "the washer and dryer, the dishwasher, the oven drawer, "
                          "the crawl space, the attic hatch, the garage rafters, "
                          "the shed, under the deck, the side of the house. This is "
                          "where things get left.",
            },
            {
                "id": "broom",
                "title": "Leave it broom clean",
                "detail": "Floors swept, carpets vacuumed, surfaces wiped, "
                          "nothing left behind. Nothing out at the curb either: "
                          "what you leave for the rubbish becomes the buyer's "
                          "problem and, often enough, your bill. If the agreement "
                          "asks for more than broom clean, do what it says.",
            },
            {
                "id": "leave-pack",
                "title": "Leave a pack on the kitchen counter",
                "detail": "This is the part sellers are remembered for. Appliance "
                          "manuals and warranties, the alarm code and the "
                          "monitoring company, the leftover paint labelled by room, "
                          "the extra tiles and flooring, the pool or spa "
                          "instructions, the garbage and recycling days, the "
                          "septic or well paperwork, and the trades you would call "
                          "again. It costs you nothing and it is the difference "
                          "between a house and a handover.",
                "list": [
                    "Manuals and warranties",
                    "Alarm code and monitoring company",
                    "Leftover paint, labelled by room",
                    "Spare tiles and flooring",
                    "Pool, spa, septic or well notes",
                    "Garbage and recycling days",
                    "Trades worth calling again",
                ],
            },
            {
                "id": "photos",
                "title": "Photograph the empty house",
                "detail": "Every room, the garage, the yard. Five minutes now, and "
                          "any argument about the condition you left it in is over "
                          "before it starts.",
            },
        ],
    },
    {
        "key": "closing",
        "offset": 0,
        "label": "Closing day",
        "lede": "Short list. Mostly it is your lawyer's day.",
        "items": [
            {
                "id": "keys-drop",
                "title": "Get every key to your lawyer",
                "detail": "First thing in the morning, unless they told you "
                          "otherwise. Label them. The buyer cannot get in until the "
                          "money has moved and the house is in their name, and your "
                          "keys are the last thing anybody is waiting on.",
            },
            {
                "id": "reachable",
                "title": "Stay reachable",
                "detail": "Deals close on the day but rarely at a set hour, and if "
                          "something needs a signature it needs it quickly.",
            },
            {
                "id": "hold-insurance",
                "title": "Still do not cancel your insurance",
                "detail": "Wait until your lawyer confirms the house is in the "
                          "buyer's name and the money has been released. That "
                          "message is the moment it stops being your risk.",
                "critical": True,
            },
        ],
    },
    {
        "key": "after",
        "offset": -7,
        "label": "The week after",
        "lede": "Three things, then it is finished.",
        "items": [
            {
                "id": "cancel-insurance",
                "title": "Now cancel the insurance",
                "detail": "Once your lawyer has confirmed it closed. Ask for the "
                          "refund of whatever you prepaid.",
            },
            {
                "id": "final-bills",
                "title": "Watch for the final bills",
                "detail": "These accounts close on a meter reading, not on the "
                          "day you call, so the last bill turns up a few weeks "
                          "later at your forwarded address. Check it against the "
                          "photos you took.",
            },
            {
                "id": "keep-papers",
                "title": "Keep the closing package somewhere you will find it",
                "detail": "The final money summary and your lawyer's closing "
                          "letter are tax records. Keep them with the paperwork "
                          "from when you bought the place.",
            },
            {
                "id": "cra",
                "title": "Report the sale on next year's tax return",
                "detail": "Every home sale has to be reported, even when you owe "
                          "no tax on it because it was the place you lived. Not "
                          "reporting it can cost one hundred dollars a month up to "
                          "eight thousand. Your accountant needs the date you "
                          "bought, the date you sold, and both prices.",
                "src": ["cra_principal", "cra_tips"],
                "link": ("Reporting the sale of your principal residence",
                         "https://www.canada.ca/en/revenue-agency/news/newsroom/tax-tips"
                         "/tax-filing-season-media-kit/tfsmk27.html"),
                "critical": True,
            },
        ],
    },
]


def all_item_ids():
    """Every id, for the progress store. Ids must be stable across builds or a
    seller's ticks move to the wrong lines when the content changes."""
    out = []
    for p in PHASES:
        for it in p["items"]:
            out.append(f"{p['key']}.{it['id']}")
    return out


def check_ids_unique():
    ids = all_item_ids()
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise SystemExit(f"duplicate item ids, progress would collide: {dupes}")
    return len(ids)
