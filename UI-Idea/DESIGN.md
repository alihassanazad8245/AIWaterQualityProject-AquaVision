---
name: Scientific Water AI System
colors:
  surface: '#fcf8fd'
  surface-dim: '#dcd9de'
  surface-bright: '#fcf8fd'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f2f7'
  surface-container: '#f0ecf2'
  surface-container-high: '#ebe7ec'
  surface-container-highest: '#e5e1e6'
  on-surface: '#1c1b1f'
  on-surface-variant: '#47464f'
  inverse-surface: '#313034'
  inverse-on-surface: '#f3eff5'
  outline: '#787680'
  outline-variant: '#c8c5d0'
  surface-tint: '#5b598e'
  primary: '#58568c'
  on-primary: '#ffffff'
  primary-container: '#716fa6'
  on-primary-container: '#fffcff'
  inverse-primary: '#c3c1fd'
  secondary: '#515d82'
  on-secondary: '#ffffff'
  secondary-container: '#c6d3fe'
  on-secondary-container: '#4e5b7f'
  tertiary: '#61603f'
  on-tertiary: '#ffffff'
  tertiary-container: '#afad86'
  on-tertiary-container: '#424122'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e3dfff'
  primary-fixed-dim: '#c3c1fd'
  on-primary-fixed: '#171447'
  on-primary-fixed-variant: '#434175'
  secondary-fixed: '#dae2ff'
  secondary-fixed-dim: '#b9c6ef'
  on-secondary-fixed: '#0b1a3b'
  on-secondary-fixed-variant: '#394669'
  tertiary-fixed: '#e7e4ba'
  tertiary-fixed-dim: '#cbc8a0'
  on-tertiary-fixed: '#1d1d03'
  on-tertiary-fixed-variant: '#494829'
  background: '#fcf8fd'
  on-background: '#1c1b1f'
  surface-variant: '#e5e1e6'
typography:
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  telemetry-num:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.05em
  telemetry-lg:
    fontFamily: JetBrains Mono
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: 0.02em
  meta-id:
    fontFamily: Space Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.1em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1.5rem
  margin: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system is engineered for a modern academic water research laboratory and AI-driven telemetry dashboard. The brand personality is rigorous, empirical, and advanced, evoking an emotional response of absolute precision, intellectual clarity, and reliable innovation. 

The aesthetic draws from a calculated blend of **Minimalism** and **Modern Corporate/Technical** principles. It relies on heavy, purposeful whitespace, exceptionally clean structural lines, and a deliberate separation between human-centric interface elements and raw, machine-generated telemetry. Every visual element serves the singular purpose of reducing cognitive load for researchers analyzing complex hydrological datasets and real-time AI model predictions.

## Colors

The color palette is meticulously calibrated for high-precision scientific environments. Muted Indigo serves as the primary structural anchor, guiding focal points and primary interactive states. Soft Blue provides contextual highlights for data streams and secondary UI layers, while Pale Cream acts as a warm, low-glare accent for active telemetry alerts and status tags. 

Dark Charcoal provides uncompromising contrast for primary typography and high-density data readouts. Pure White and Silver define the structural canvas and surface containers, establishing a pristine, clinical backdrop that prevents visual fatigue during extended analysis sessions.

## Typography

The typographical hierarchy clearly delineates human navigation from machine telemetry. **Plus Jakarta Sans** provides a welcoming yet precise structural frame for all core UI elements, dashboard navigation, and academic reports. 

Numerical data, real-time sensor readouts, and quantitative metrics are strictly rendered in **JetBrains Mono** to ensure tabular alignment and immediate legibility at a glance. Hardware identifiers, sensor nodes, and technical metadata utilize **Space Mono**, establishing an immediate visual cue for system architecture and hardware topology.

## Layout & Spacing

The layout relies on a strict 12-column fluid grid system designed to maximize screen real estate for complex data visualizations and multi-parameter sensor arrays. Outer canvas margins remain fixed at 2rem on desktop, contracting to 1rem on mobile viewpoints, while internal column gutters are maintained at a uniform 1.5rem to establish clear separation between telemetry cards.

Content reflow prioritizes card-based modularity: multi-column research panels collapse into single-column vertical stacks on mobile viewports, while telemetry data tables introduce horizontal scrolling with sticky header columns to preserve quantitative context.

## Elevation & Depth

Visual hierarchy is communicated entirely through **low-contrast outlines** and structured tonal layering rather than heavy drop shadows. Surface containers utilize pure white backgrounds separated from the silver canvas by ultra-fine, low-opacity borders using Dark Charcoal. 

Depth is achieved by shifting surface container values incrementally between white and soft neutral tints, keeping the interface resolutely flat, clinical, and data-forward. Interactive states introduce subtle surface tint shifts rather than physical elevation.

## Shapes

The design system implements a **Soft** geometric shape language with a baseline roundedness of 0.25rem for micro-components, scaling to 0.5rem (`rounded-lg`) for standard cards and containers. This slight softening removes clinical harshness while maintaining a precise, engineered appearance that avoids overly playful or consumer-grade aesthetics.

## Components

### Buttons
Primary actions utilize Muted Indigo backgrounds with crisp typography, featuring soft-rounded corners and subtle hover state shifts to Soft Blue. Secondary and tertiary actions rely on ghost configurations with fine neutral borders, ensuring analytical tools never visually overpower raw data inputs.

### Chips & Tags
Compact indicator elements for sensor status, AI confidence scores, and water quality parameters. Rendered in fixed-height pills using JetBrains Mono for internal numerical thresholds, paired with Pale Cream or Soft Blue background tints.

### Input Fields & Parameters
Form controls and threshold entry fields feature high-contrast Dark Charcoal borders, white backgrounds, and internal monospaced typography for numeric constraints. Focus states display a crisp Muted Indigo outline with zero blur spread.

### Cards & Telemetry Containers
The core building blocks of the dashboard. Cards feature a pure white surface, subtle 1px neutral borders, and structured internal padding. Header regions cleanly separate human labels (Plus Jakarta Sans) from hardware IDs (Space Mono) and live sensor streams (JetBrains Mono).

### Checkboxes & Radio Controls
Engineered with precise geometric squares and circles, utilizing zero roundedness for structural toggles to emphasize technical exactness, paired with high-contrast active states.

### Specialized Components
- **TimeSeries Sparklines:** Inline mini-charts integrated directly into data tables for rapid anomaly detection.
- **Node Topology Maps:** Interactive schematic viewers utilizing Space Mono metadata for hardware tracking.
- **AI Confidence Meters:** Segmented progress bars visualizing predictive water flow models with real-time probabilistic readouts.