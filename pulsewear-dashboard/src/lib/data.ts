// ============================================================
// PulseWear Labs — Static Mock Data
// Based on real cluster descriptions from pulsewear_clustered_data.csv
// ============================================================

export interface Theme {
  cluster_id: number;
  name: string;
  description: string;
  volume: number;
  positive_pct: number;
  negative_pct: number;
  roadmap_id: string | null;
  priority_score: number; // 0-100, derived from volume + negative sentiment
}

export interface ChannelStat {
  name: string;
  count: number;
  pct: number;
}

export interface SummaryStats {
  total_feedback: number;
  positive_pct: number;
  negative_pct: number;
  active_themes: number;
}

export interface AccountProfile {
  initials: string;
  name: string;
  role: string;
  email: string;
  team: string;
  location: string;
  plan: string;
}

export interface MonthlyDataPoint {
  month: string;        // e.g. "Mar 2024"
  month_short: string;  // e.g. "Mar"
  volumes: number[];    // volume per cluster (index = cluster_id)
}

export interface RoadmapItem {
  roadmap_id: string;
  cluster_id: number;
  theme_name: string;
  volume: number;
  positive_pct: number;
  priority_score: number;
  status: 'Active' | 'Planned' | 'Under Review' | 'Backlog';
}

// ── Summary Stats ─────────────────────────────────────────────
export const summaryStats: SummaryStats = {
  total_feedback: 20000,
  positive_pct: 62,
  negative_pct: 38,
  active_themes: 10
};

export const accountProfile: AccountProfile = {
  initials: 'EB',
  name: 'Ethan Brooks',
  role: 'Product Insights Lead',
  email: 'ethan.brooks@pulsewearlabs.com',
  team: 'Customer Feedback Intelligence',
  location: 'Boston, MA',
  plan: 'Admin access'
};

// ── Themes (10 clusters) ──────────────────────────────────────
export const themes: Theme[] = [
  {
    cluster_id: 0,
    name: 'Fitness & Social Features',
    description: 'Workout tracking, social sharing, avatar customization, community challenges',
    volume: 2340,
    positive_pct: 71,
    negative_pct: 29,
    roadmap_id: 'PWL-ROAD-01',
    priority_score: 72,
  },
  {
    cluster_id: 1,
    name: 'Battery & Connectivity',
    description: 'Battery drain, Bluetooth lag, GPS connectivity, sync failures',
    volume: 2180,
    positive_pct: 32,
    negative_pct: 68,
    roadmap_id: 'PWL-ROAD-02',
    priority_score: 94,
  },
  {
    cluster_id: 2,
    name: 'Multi-User & Privacy',
    description: 'Family profiles, data sharing controls, privacy settings, subscription value',
    volume: 1950,
    positive_pct: 58,
    negative_pct: 42,
    roadmap_id: 'PWL-ROAD-03',
    priority_score: 58,
  },
  {
    cluster_id: 3,
    name: 'Customer Support & Setup',
    description: 'Onboarding flow, pairing issues, support response time, documentation',
    volume: 1820,
    positive_pct: 44,
    negative_pct: 56,
    roadmap_id: 'PWL-ROAD-04',
    priority_score: 76,
  },
  {
    cluster_id: 4,
    name: 'Notifications & Alerts',
    description: 'Push notification timing, alert customization, do-not-disturb, smart reminders',
    volume: 2100,
    positive_pct: 65,
    negative_pct: 35,
    roadmap_id: 'PWL-ROAD-05',
    priority_score: 54,
  },
  {
    cluster_id: 5,
    name: 'General Feedback',
    description: 'Mixed general satisfaction, vague praise, average experience comments',
    volume: 1640,
    positive_pct: 55,
    negative_pct: 45,
    roadmap_id: null,
    priority_score: 20,
  },
  {
    cluster_id: 6,
    name: 'Water Resistance & Durability',
    description: 'Swim tracking, waterproof rating, physical durability, strap comfort',
    volume: 1980,
    positive_pct: 69,
    negative_pct: 31,
    roadmap_id: 'PWL-ROAD-06',
    priority_score: 48,
  },
  {
    cluster_id: 7,
    name: 'App & Firmware Updates',
    description: 'Update-related friction, transition-period complaints, version rollout feedback',
    volume: 1560,
    positive_pct: 48,
    negative_pct: 52,
    roadmap_id: null,
    priority_score: 18,
  },
  {
    cluster_id: 8,
    name: 'Data Security & Health',
    description: 'Health data encryption, HIPAA concerns, third-party sharing, account security',
    volume: 2220,
    positive_pct: 41,
    negative_pct: 59,
    roadmap_id: 'PWL-ROAD-07',
    priority_score: 88,
  },
  {
    cluster_id: 9,
    name: 'Premium Features & Updates',
    description: 'Premium tier value, firmware update quality, new feature requests, OS compatibility',
    volume: 2210,
    positive_pct: 60,
    negative_pct: 40,
    roadmap_id: 'PWL-ROAD-08',
    priority_score: 62,
  }
];

// ── Channel Breakdown ─────────────────────────────────────────
export const channels: ChannelStat[] = [
  { name: 'App Review',     count: 5600, pct: 28 },
  { name: 'Support Ticket', count: 4800, pct: 24 },
  { name: 'Social Media',   count: 5200, pct: 26 },
  { name: 'Beta Testing',   count: 4400, pct: 22 },
];

// ── Monthly Trend Data (Mar 2024 – Feb 2025) ──────────────────
// volumes[i] = volume for cluster_id i in that month
export const monthlyTrends: MonthlyDataPoint[] = [
  { month: 'Mar 2024', month_short: 'Mar', volumes: [165, 190, 142, 138, 148, 110, 145, 112, 160, 158] },
  { month: 'Apr 2024', month_short: 'Apr', volumes: [172, 198, 148, 142, 156, 112, 150, 115, 168, 164] },
  { month: 'May 2024', month_short: 'May', volumes: [180, 210, 152, 148, 162, 115, 158, 118, 175, 172] },
  { month: 'Jun 2024', month_short: 'Jun', volumes: [188, 205, 158, 155, 168, 118, 165, 122, 182, 180] },
  { month: 'Jul 2024', month_short: 'Jul', volumes: [195, 215, 162, 160, 175, 120, 170, 125, 192, 188] },
  { month: 'Aug 2024', month_short: 'Aug', volumes: [200, 225, 165, 162, 178, 122, 172, 128, 198, 192] },
  { month: 'Sep 2024', month_short: 'Sep', volumes: [192, 220, 160, 158, 172, 118, 168, 124, 194, 186] },
  { month: 'Oct 2024', month_short: 'Oct', volumes: [198, 228, 168, 164, 180, 125, 175, 130, 200, 195] },
  { month: 'Nov 2024', month_short: 'Nov', volumes: [205, 232, 172, 168, 185, 128, 178, 133, 208, 202] },
  { month: 'Dec 2024', month_short: 'Dec', volumes: [210, 240, 175, 170, 190, 130, 180, 135, 215, 210] },
  { month: 'Jan 2025', month_short: 'Jan', volumes: [218, 235, 178, 168, 185, 127, 177, 132, 212, 205] },
  { month: 'Feb 2025', month_short: 'Feb', volumes: [215, 232, 175, 165, 182, 125, 175, 130, 208, 198] },
];

// Helper: compute month-over-month change for a cluster
export function getTrend(clusterId: number): number {
  const last = monthlyTrends[monthlyTrends.length - 1].volumes[clusterId];
  const prev = monthlyTrends[monthlyTrends.length - 2].volumes[clusterId];
  return Math.round(((last - prev) / prev) * 100);
}

// ── Roadmap Items ─────────────────────────────────────────────
export const roadmapItems: RoadmapItem[] = [
  { roadmap_id: 'PWL-ROAD-02', cluster_id: 1, theme_name: 'Battery & Connectivity',      volume: 2180, positive_pct: 32, priority_score: 94, status: 'Active' },
  { roadmap_id: 'PWL-ROAD-07', cluster_id: 8, theme_name: 'Data Security & Health',       volume: 2220, positive_pct: 41, priority_score: 88, status: 'Active' },
  { roadmap_id: 'PWL-ROAD-04', cluster_id: 3, theme_name: 'Customer Support & Setup',     volume: 1820, positive_pct: 44, priority_score: 76, status: 'Active' },
  { roadmap_id: 'PWL-ROAD-01', cluster_id: 0, theme_name: 'Fitness & Social Features',    volume: 2340, positive_pct: 71, priority_score: 72, status: 'Active' },
  { roadmap_id: 'PWL-ROAD-08', cluster_id: 9, theme_name: 'Premium Features & Updates',   volume: 2210, positive_pct: 60, priority_score: 62, status: 'Planned' },
  { roadmap_id: 'PWL-ROAD-03', cluster_id: 2, theme_name: 'Multi-User & Privacy',         volume: 1950, positive_pct: 58, priority_score: 58, status: 'Planned' },
  { roadmap_id: 'PWL-ROAD-05', cluster_id: 4, theme_name: 'Notifications & Alerts',       volume: 2100, positive_pct: 65, priority_score: 54, status: 'Under Review' },
  { roadmap_id: 'PWL-ROAD-06', cluster_id: 6, theme_name: 'Water Resistance & Durability',volume: 1980, positive_pct: 69, priority_score: 48, status: 'Backlog' },
];

// ── Sample Feedback Quotes ─────────────────────────────────────
export const sampleFeedback: Record<number, { text: string; sentiment: 'POSITIVE' | 'NEGATIVE'; channel: string }[]> = {
  0: [
    { text: 'Love the new run tracking — comparing splits with friends is amazing!', sentiment: 'POSITIVE', channel: 'App Review' },
    { text: 'The community challenges keep me motivated every single week.', sentiment: 'POSITIVE', channel: 'Social Media' },
    { text: 'Wish the avatar builder had more customization options.', sentiment: 'NEGATIVE', channel: 'App Review' },
    { text: 'The social leaderboard is a great motivator during marathon training.', sentiment: 'POSITIVE', channel: 'Beta Testing' },
    { text: 'Group workout mode keeps crashing when more than 4 people join.', sentiment: 'NEGATIVE', channel: 'Support Ticket' },
    { text: 'Finally an app that makes fitness fun with friends!', sentiment: 'POSITIVE', channel: 'Social Media' },
  ],
  1: [
    { text: 'Battery is dead by 6pm every day. Barely usable.', sentiment: 'NEGATIVE', channel: 'App Review' },
    { text: 'GPS drops out constantly on my morning run.', sentiment: 'NEGATIVE', channel: 'Support Ticket' },
    { text: 'Bluetooth disconnects from my phone at least twice a day.', sentiment: 'NEGATIVE', channel: 'App Review' },
    { text: 'After the latest update my battery life improved by 20%. Thank you!', sentiment: 'POSITIVE', channel: 'App Review' },
    { text: 'Sync fails every morning — I have to unpair and re-pair constantly.', sentiment: 'NEGATIVE', channel: 'Support Ticket' },
    { text: 'Worst battery life of any wearable I have owned. Unacceptable for the price.', sentiment: 'NEGATIVE', channel: 'Social Media' },
  ],
  2: [
    { text: 'Would love a family plan — paying for 4 separate subscriptions is expensive.', sentiment: 'NEGATIVE', channel: 'App Review' },
    { text: 'Please add granular privacy controls for health data sharing.', sentiment: 'NEGATIVE', channel: 'Support Ticket' },
    { text: 'The multi-device sync is actually working well now!', sentiment: 'POSITIVE', channel: 'Beta Testing' },
    { text: 'My kids and I all use PulseWear — a family dashboard would be perfect.', sentiment: 'POSITIVE', channel: 'Social Media' },
    { text: 'I cannot find where to turn off third-party data sharing. This is a concern.', sentiment: 'NEGATIVE', channel: 'Support Ticket' },
    { text: 'Profile switching between family members is seamless.', sentiment: 'POSITIVE', channel: 'App Review' },
  ],
  3: [
    { text: 'Took 3 hours and two support calls to pair the device. Terrible experience.', sentiment: 'NEGATIVE', channel: 'Support Ticket' },
    { text: 'Support team was patient and resolved my issue in one call.', sentiment: 'POSITIVE', channel: 'Support Ticket' },
    { text: 'The quick-start guide is outdated and confusing.', sentiment: 'NEGATIVE', channel: 'App Review' },
    { text: 'Setup wizard needs a complete redesign — I gave up halfway through.', sentiment: 'NEGATIVE', channel: 'App Review' },
    { text: 'Great support agent helped me set up health tracking — very satisfied.', sentiment: 'POSITIVE', channel: 'Support Ticket' },
    { text: 'Why is there no video tutorial for initial device setup?', sentiment: 'NEGATIVE', channel: 'Social Media' },
  ],
  4: [
    { text: 'Smart notifications are perfectly timed — not too many, not too few.', sentiment: 'POSITIVE', channel: 'App Review' },
    { text: 'I keep missing important alerts because they bundle too aggressively.', sentiment: 'NEGATIVE', channel: 'App Review' },
    { text: 'Do-not-disturb integration with my calendar is a game changer.', sentiment: 'POSITIVE', channel: 'Beta Testing' },
    { text: 'Way too many notifications — I turned them all off.', sentiment: 'NEGATIVE', channel: 'App Review' },
    { text: 'The activity reminder nudges actually got me moving more throughout the day.', sentiment: 'POSITIVE', channel: 'Social Media' },
    { text: 'Notification grouping logic is broken — I get duplicates.', sentiment: 'NEGATIVE', channel: 'Support Ticket' },
  ],
  5: [
    { text: 'It is okay. Does the basics well but nothing stands out.', sentiment: 'POSITIVE', channel: 'App Review' },
    { text: 'Average product. Expected more for the price.', sentiment: 'NEGATIVE', channel: 'App Review' },
    { text: 'Solid device overall, nothing groundbreaking.', sentiment: 'POSITIVE', channel: 'Social Media' },
    { text: 'Works as advertised. Not impressed but not disappointed either.', sentiment: 'POSITIVE', channel: 'App Review' },
  ],
  6: [
    { text: 'Wore it in the ocean for a week — still working flawlessly.', sentiment: 'POSITIVE', channel: 'Beta Testing' },
    { text: 'The 5ATM rating held up during lap swimming. Impressed.', sentiment: 'POSITIVE', channel: 'App Review' },
    { text: 'The silicone band irritates my wrist after long swims.', sentiment: 'NEGATIVE', channel: 'Support Ticket' },
    { text: 'Pool tracking is surprisingly accurate — stroke count and laps all correct.', sentiment: 'POSITIVE', channel: 'App Review' },
    { text: 'The coating on the screen scratched after a week of water sports.', sentiment: 'NEGATIVE', channel: 'Social Media' },
    { text: 'Best swim tracking I have used on any wearable.', sentiment: 'POSITIVE', channel: 'Social Media' },
  ],
  7: [
    { text: 'It is okay I guess. Not great, not terrible.', sentiment: 'POSITIVE', channel: 'App Review' },
    { text: 'Mediocre product. Expected better from PulseWear.', sentiment: 'NEGATIVE', channel: 'App Review' },
    { text: 'Decent for the price but there are better alternatives.', sentiment: 'NEGATIVE', channel: 'Social Media' },
    { text: 'Not sure how I feel about it yet — been using it for a month.', sentiment: 'POSITIVE', channel: 'App Review' },
  ],
  8: [
    { text: 'I am uncomfortable with how health data is shared with third parties.', sentiment: 'NEGATIVE', channel: 'Support Ticket' },
    { text: 'Appreciate the new HIPAA compliance updates in the last firmware.', sentiment: 'POSITIVE', channel: 'App Review' },
    { text: 'Two-factor authentication finally added — thank you!', sentiment: 'POSITIVE', channel: 'App Review' },
    { text: 'My health data was accessible after I sold my old device. This is unacceptable.', sentiment: 'NEGATIVE', channel: 'Support Ticket' },
    { text: 'End-to-end encryption for health metrics would make me much more comfortable.', sentiment: 'NEGATIVE', channel: 'Social Media' },
    { text: 'The new data export feature with encryption is excellent.', sentiment: 'POSITIVE', channel: 'Beta Testing' },
  ],
  9: [
    { text: 'The premium tier feels overpriced for what you get.', sentiment: 'NEGATIVE', channel: 'App Review' },
    { text: 'New firmware update broke sleep tracking for a week.', sentiment: 'NEGATIVE', channel: 'Support Ticket' },
    { text: 'ECG feature added in the latest update is exceptional.', sentiment: 'POSITIVE', channel: 'App Review' },
    { text: 'Premium subscription auto-renewed without a reminder. Check your emails.', sentiment: 'NEGATIVE', channel: 'Support Ticket' },
    { text: 'The OS 14 compatibility update was well done — no issues at all.', sentiment: 'POSITIVE', channel: 'Beta Testing' },
    { text: 'Every update seems to introduce two new bugs. QA needs work.', sentiment: 'NEGATIVE', channel: 'Social Media' },
  ]
};
