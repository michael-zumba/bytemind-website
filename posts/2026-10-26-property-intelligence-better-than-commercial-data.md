---
title: "Better than commercial property data? What a range-first model can and cannot claim"
date: 2026-10-26
summary: "Most automated property estimates give one number and no error. A range-first model is not more precise - it is more honest about what it knows. Here is what that can support, and the claims it does not support."
---

## Summary

Automated property estimates have become part of how New Zealand property is discussed, priced and marketed. Most of them share a design choice: return one confident-looking number. That is easy to consume and easy to sell, but it is a poor input to a decision, because it hides the two things a decision needs - how wrong the number might be, and where it came from.

This brief sets out what a range-first, source-attributed property model can support as evidence, and the claims it deliberately does not make. It documents the independent research project at [Auckland Property Scout](/reports/property-intelligence/).

## The problem with a single number

A point estimate of, say, $1.46 million invites a decision that the underlying evidence may not support. If two comparable homes are $40,000 apart, is that a real difference, a date effect, or model noise? Without an error term or a source, there is no way to tell. The number is precise, but precision is not accuracy, and neither is the same thing as usefulness.

Three consequences follow, and they are a property of the category rather than a charge against any particular vendor:

- **No error bar.** A single figure cannot be used to set a negotiation buffer or to argue a range in a client conversation.
- **No provenance.** When the inputs and weights are invisible, you cannot tell whether the value describes the property or the model's habits, and you cannot audit it later.
- **No date honesty.** A market that reprices weekly, summarised by a quarterly median, is a lagging indicator dressed as a current one.

## What a range-first model actually produces

The model behind Property Intelligence starts from the signals that are publicly visible on a listing page: a Homes.co.nz automated valuation range where one exists, the council capital value with its land and improvement split, and the nearby sales shown with the listing. It does not invent a value where no signal exists.

Those signals are then handled in a hierarchy rather than blended into secrecy:

1. **A published third-party AVM range**, with its update date, where one exists.
2. **An independent comparable-sales range**, built from nearby sold prices weighted by distance, recency, property type and same-suburb, and normalised by council CV so that a small unit and a large house are compared on the same basis.
3. **A labelled fallback** for properties the AVM cannot match: a hedonic model with an empirical 80% interval, calibrated on out-of-fold residuals, plus a weaker no-CV variant that is stated as weaker.
4. **The council CV as a cross-check**, never as market value.

Coverage is not universal. In the current snapshot, about half of the standard listings carry a Homes.co.nz estimate; the rest are handled by the comparable model or a clearly labelled fallback. The comparable pool is built from the nearby-sales cards shown on listing pages - a small, de-duplicated sample, not a complete sales register. That limits how tight a comparable range can honestly be.

## What the claims cannot be

A transparent model is not automatically a better model, and this one is careful about its limits:

- **Not a valuation under professional standards.** It is decision support. Where a valuation is required - for lending, legal or insurance purposes - a registered valuer must provide it.
- **Not advice and not a forecast.** No figure is a prediction of return. Automated estimates carry error, including the calibrated fallback whose error is published.
- **A snapshot, not a live feed.** It refreshes daily, but it is still a snapshot; the date matters.
- **Tenure is inferred, not confirmed.** Leasehold and cross-lease interests are detected from listing text, not title records. The title and any ground rent need checking before an offer.
- **The methodology has not been independently audited.** It is documented and reproducible, which is not the same thing as externally validated.

## Why the working matters

For a buyer, the value is a defensible negotiation range instead of an anchor. For an adviser or professional-service firm, the value is that a number can be explained to a client and, if challenged, traced: which source produced it, what the error is, when it was published, and what the model could not see.

That is a different kind of evidence from a single price. It is also a more honest one: the model shows its gaps rather than smoothing over them. A range with a stated error is less satisfying than a confident number, but it is the better input to a decision.

## Check the working

The live interface, the market view and the research lab are public, and every figure on the product page hydrates from a published snapshot rather than from copy written by hand:

- [Auckland Property Scout](/reports/property-intelligence/) - method, market snapshot and limits
- [Open the property app](/reports/property-intelligence/app/) - map, market view and research lab
- [Long-run property market research](/reports/property-market-analysis/) - the macro backdrop this work sits inside

The methodology, limits and source notes are published with the project. This is independent research, not a commercial service.
