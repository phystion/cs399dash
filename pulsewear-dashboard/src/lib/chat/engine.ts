import { channels, monthlyTrends, roadmapItems, themes } from '$lib/data';

export interface AssistantMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AssistantReply {
  reply: string;
  sources: string[];
  clusterId: number | null;
}

const themeById = new Map(themes.map((theme) => [theme.cluster_id, theme]));
const roadmapByCluster = new Map(roadmapItems.map((item) => [item.cluster_id, item]));
const themeVolumeTotal = themes.reduce((sum, theme) => sum + theme.volume, 0);
const channelVolumeTotal = channels.reduce((sum, channel) => sum + channel.count, 0);
const totalFeedback = themeVolumeTotal || channelVolumeTotal;
const weightedPositiveTotal = themes.reduce((sum, theme) => sum + (theme.volume * theme.positive_pct), 0);
const overallPositivePct = totalFeedback > 0 ? Math.round(weightedPositiveTotal / totalFeedback) : 0;
const overallNegativePct = totalFeedback > 0 ? 100 - overallPositivePct : 0;
const themesByPriority = [...themes].sort((a, b) => b.priority_score - a.priority_score);
const starterTheme = themesByPriority[0] ?? themes[0] ?? null;
const compareThemes = themesByPriority.slice(0, 2);
const compareThemeA = compareThemes[0] ?? themes[0] ?? null;
const compareThemeB = compareThemes[1] ?? themes[1] ?? themes[0] ?? null;

const STOPWORDS = new Set([
  'about', 'after', 'alerts', 'analysis', 'and', 'app', 'are', 'assistant', 'best',
  'between', 'cluster', 'clusters', 'compare', 'comparison', 'current', 'data', 'dashboard',
  'describe', 'details', 'feedback', 'for', 'from', 'give', 'have', 'help', 'how', 'i',
  'improve', 'issue', 'issues', 'just', 'latest', 'management', 'me', 'more', 'most',
  'new', 'next', 'page', 'please', 'priority', 'priorities', 'project', 'pulsewear',
  'roadmap', 'show', 'status', 'summary', 'tell', 'that', 'the', 'theme', 'themes',
  'this', 'ticket', 'top', 'trend', 'trends', 'users', 'versus', 'vs', 'what', 'which'
]);

function normalizeToken(token: string): string {
  let normalized = token.toLowerCase();

  if (normalized.endsWith('ies') && normalized.length > 4) {
    normalized = `${normalized.slice(0, -3)}y`;
  } else if (normalized.endsWith('s') && normalized.length > 4) {
    normalized = normalized.slice(0, -1);
  }

  return normalized;
}

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .match(/[a-z0-9]+/g)
    ?.map(normalizeToken)
    .filter((token) => token.length >= 3 && !STOPWORDS.has(token)) ?? [];
}

function buildThemeKeywords(themeId: number): Set<string> {
  const theme = themeById.get(themeId);
  if (!theme) return new Set();

  return new Set([
    ...tokenize(theme.name),
    ...tokenize(theme.description),
    ...(theme.roadmap_id ? tokenize(theme.roadmap_id) : [])
  ]);
}

const themeKeywords = new Map(themes.map((theme) => [theme.cluster_id, buildThemeKeywords(theme.cluster_id)]));

export const chatPageStarters = [
  'What are the top 3 issues I should focus on this quarter?',
  starterTheme ? `Summarize ${starterTheme.name} feedback in 2 sentences.` : 'Summarize the top priority theme in 2 sentences.',
  'Which roadmap items are active right now?',
  'Show the Jira ticket template for the top issue.',
  compareThemeA && compareThemeB
    ? `Compare ${compareThemeA.name} vs ${compareThemeB.name}.`
    : 'Compare the top two themes.',
  starterTheme ? `What percentage of users are unhappy with ${starterTheme.name}?` : 'What percentage of users are unhappy with the top priority theme?'
];

export const popupStarters = [
  'Top 3 priorities?',
  starterTheme ? `${starterTheme.name} summary` : 'Top theme summary',
  'Roadmap status'
];

function findLastMentionedCluster(history: AssistantMessage[]): number | null {
  for (let i = history.length - 1; i >= 0; i -= 1) {
    const [themeId] = detectThemes(history[i].content);
    if (themeId !== undefined) return themeId;
  }

  return null;
}

function detectThemes(text: string): number[] {
  const queryTokens = new Set(tokenize(text));
  const lowerText = text.toLowerCase();
  const scoredThemes = themes
    .map((theme) => {
      let score = 0;

      if (lowerText.includes(theme.name.toLowerCase())) score += 100;
      if (theme.roadmap_id && lowerText.includes(theme.roadmap_id.toLowerCase())) score += 80;
      if (new RegExp(`\\bcluster\\s+${theme.cluster_id}\\b`, 'i').test(text)) score += 90;

      for (const keyword of themeKeywords.get(theme.cluster_id) ?? []) {
        if (queryTokens.has(keyword)) score += keyword.length >= 7 ? 3 : 2;
      }

      return { themeId: theme.cluster_id, score };
    })
    .filter(({ score }) => score >= 2)
    .sort((a, b) => b.score - a.score);

  return scoredThemes.map(({ themeId }) => themeId);
}

function clusterDetail(clusterId: number): AssistantReply {
  const theme = themeById.get(clusterId);
  if (!theme) {
    return {
      reply: 'I could not resolve that cluster from the current dashboard data.',
      sources: [],
      clusterId: null
    };
  }

  const roadmap = roadmapByCluster.get(clusterId);
  const roadmapLabel = roadmap ? `${roadmap.roadmap_id} (${roadmap.status})` : 'no roadmap item';

  return {
    reply:
      `Cluster ${theme.cluster_id} — ${theme.name}: ${theme.volume.toLocaleString()} entries, ` +
      `${theme.positive_pct}% positive / ${theme.negative_pct}% negative, priority score ${theme.priority_score}/100. ` +
      `Roadmap: ${roadmapLabel}. Key topics: ${theme.description}.`,
    sources: [`cluster:${theme.cluster_id}`, ...(roadmap ? [roadmap.roadmap_id] : [])],
    clusterId
  };
}

function monthVolume(clusterId: number, monthIndex: number) {
  return monthlyTrends[monthIndex]?.volumes[clusterId] ?? 0;
}

function peakMonth(clusterId: number) {
  if (monthlyTrends.length === 0) {
    return { month: '', volume: 0 };
  }

  return monthlyTrends.reduce(
    (best, month) => (month.volumes[clusterId] > best.volume ? { month: month.month, volume: month.volumes[clusterId] } : best),
    { month: monthlyTrends[0]?.month ?? '', volume: monthVolume(clusterId, 0) }
  );
}

function latestTrend(clusterId: number) {
  const latest = monthVolume(clusterId, monthlyTrends.length - 1);
  const previous = monthVolume(clusterId, monthlyTrends.length - 2);
  const delta = latest - previous;
  const deltaPct = previous > 0 ? Math.round((delta / previous) * 100) : 0;

  return { latest, previous, delta, deltaPct };
}

function ticketTemplate(themeId: number): AssistantReply {
  const theme = themeById.get(themeId);
  if (!theme) {
    return {
      reply: 'I could not build a ticket template for that theme.',
      sources: [],
      clusterId: null
    };
  }

  const roadmap = roadmapByCluster.get(themeId);
  const issueAreas = theme.description.split(',').map((part) => part.trim()).filter(Boolean).slice(0, 3);
  const titlePrefix = roadmap ? `[${roadmap.roadmap_id}] ` : '';
  const acceptanceCriteria = issueAreas.length > 0
    ? issueAreas.map((area) => `- Improve ${area}`).join('\n')
    : '- Reduce reported issues in the next review cycle';

  return {
    reply:
      `Ticket template for ${theme.name}:\n\n` +
      `Title: ${titlePrefix}Improve ${theme.name.replace(/&/g, 'and')}\n\n` +
      `Description:\n` +
      `${theme.name} has ${theme.volume.toLocaleString()} feedback entries, ${theme.negative_pct}% negative sentiment, and a priority score of ${theme.priority_score}/100. ` +
      `${roadmap ? `It is currently ${roadmap.status.toLowerCase()} on the roadmap. ` : ''}` +
      `${issueAreas.length > 0 ? `Main issue areas: ${issueAreas.join(', ')}.` : ''}\n\n` +
      'Acceptance Criteria:\n' +
      `${acceptanceCriteria}\n` +
      `- Lower negative sentiment from ${theme.negative_pct}% in the next review cycle`,
    sources: [`cluster:${theme.cluster_id}`, ...(roadmap ? [roadmap.roadmap_id] : [])],
    clusterId: theme.cluster_id
  };
}

function simulateLatency() {
  return new Promise<void>((resolve) => {
    setTimeout(resolve, 180);
  });
}

export async function resolveAssistantReply(messages: AssistantMessage[]): Promise<AssistantReply> {
  const lastUser = [...messages].reverse().find((message) => message.role === 'user')?.content.trim();

  if (!lastUser) {
    throw new Error('No user message found');
  }

  const history = messages.slice(0, -1);
  const lastCluster = findLastMentionedCluster(history);
  const text = lastUser.toLowerCase();

  await simulateLatency();

  if (/\b(that cluster|that one|tell me more|more about it|what about that|elaborate)\b/i.test(lastUser) && lastCluster !== null) {
    const detail = clusterDetail(lastCluster);
    return {
      reply: `Following up on the previous cluster. ${detail.reply}`,
      sources: detail.sources,
      clusterId: lastCluster
    };
  }

  if (/^\s*(hello|hi|hey|howdy|good morning|good afternoon|good evening)[!.,]?\s*$/i.test(lastUser)) {
    return {
      reply:
        'Hello, Ethan. I’m the feedback assistant. ' +
        'Ask about a theme, top issues, trends, roadmap status, or a quick summary.',
      sources: ['summary'],
      clusterId: null
    };
  }

  if (/\b(help|what can you do|capabilities|commands|what do you know)\b/i.test(lastUser)) {
    return {
      reply:
        'I can answer questions about:\n' +
        '- Top priorities and urgent issues\n' +
        '- Specific themes by name or keyword\n' +
        '- Dataset summary and sentiment leaders/laggards\n' +
        '- Roadmap status and trend shifts\n' +
        '- Channel mix and recommended next steps\n' +
        '- The ticket template for the top issue and side-by-side comparisons',
      sources: ['summary'],
      clusterId: null
    };
  }

  if (/\b(summary|overview|dataset|context|project context|what is this project)\b/i.test(lastUser)) {
    const topPriority = themesByPriority[0];
    if (!topPriority) {
      return {
        reply: 'This dashboard is running, but no theme data is loaded right now.',
        sources: ['summary'],
        clusterId: null
      };
    }

    return {
      reply:
        `This is a feedback intelligence dashboard built around local data. ` +
        `It currently tracks ${totalFeedback.toLocaleString()} feedback entries across ${themes.length} themes with ${overallPositivePct}% positive and ${overallNegativePct}% negative sentiment. ` +
        `The highest-priority theme right now is ${topPriority.name} at ${topPriority.priority_score}/100, and the assistant answers from the loaded dashboard data instead of calling an external model.`,
      sources: ['summary', `cluster:${topPriority.cluster_id}`],
      clusterId: topPriority.cluster_id
    };
  }

  if (/\b(compare|comparison|versus|vs\.?|difference between)\b/i.test(lastUser)) {
    const mentioned = detectThemes(lastUser);
    if (themes.length === 0) {
      return {
        reply: 'No theme data is loaded right now, so there is nothing to compare yet.',
        sources: ['summary'],
        clusterId: null
      };
    }

    const [firstId = compareThemeA?.cluster_id ?? themes[0].cluster_id, secondId = compareThemeB?.cluster_id ?? themes[0].cluster_id] = mentioned;
    const first = themeById.get(firstId);
    const second = themeById.get(secondId);

    if (first && second) {
      return {
        reply:
          `Comparing ${first.name} and ${second.name}:\n` +
          `- ${first.name}: ${first.volume.toLocaleString()} entries, ${first.positive_pct}% positive, priority ${first.priority_score}, roadmap ${roadmapByCluster.get(firstId)?.roadmap_id ?? 'none'}\n` +
          `- ${second.name}: ${second.volume.toLocaleString()} entries, ${second.positive_pct}% positive, priority ${second.priority_score}, roadmap ${roadmapByCluster.get(secondId)?.roadmap_id ?? 'none'}\n` +
          `${first.priority_score > second.priority_score ? first.name : second.name} is the stronger escalation target based on current dashboard priority score.`,
        sources: [`cluster:${firstId}`, `cluster:${secondId}`],
        clusterId: null
      };
    }
  }

  if (/\b(top (\d+ )?(issue|issues|priority|priorities)|focus|urgent|most critical|highest priority|what should we fix|what to fix)\b/i.test(lastUser)) {
    const topThree = themesByPriority.slice(0, 3);
    if (topThree.length === 0) {
      return {
        reply: 'No theme data is loaded right now, so I cannot rank priorities yet.',
        sources: ['summary'],
        clusterId: null
      };
    }

    return {
      reply:
        `Top ${topThree.length} priorities by dashboard urgency score:\n` +
        topThree
          .map((theme, index) => `${index + 1}. ${theme.name} (${theme.priority_score}/100, ${theme.negative_pct}% negative)`)
          .join('\n') +
        `\n${topThree[0].name} is the highest-priority area to fix first.`,
      sources: topThree.map((theme) => `cluster:${theme.cluster_id}`),
      clusterId: topThree[0].cluster_id
    };
  }

  const [matchedTheme] = detectThemes(lastUser);
  if (matchedTheme !== undefined) {
    return clusterDetail(matchedTheme);
  }

  if (/\b(best|most positive|strongest sentiment|what is working)\b/i.test(lastUser)) {
    const topPositive = [...themes].sort((a, b) => b.positive_pct - a.positive_pct).slice(0, 3);
    if (topPositive.length === 0) {
      return {
        reply: 'No theme data is loaded right now, so I cannot rank positive themes yet.',
        sources: ['summary'],
        clusterId: null
      };
    }

    return {
      reply:
        `Most positive themes:\n` +
        topPositive
          .map((theme, index) => `${index + 1}. ${theme.name} (${theme.positive_pct}% positive, ${theme.volume.toLocaleString()} entries)`)
          .join('\n') +
        `\n${topPositive[0].name} is the clearest product strength in the current data.`,
      sources: topPositive.map((theme) => `cluster:${theme.cluster_id}`),
      clusterId: topPositive[0].cluster_id
    };
  }

  if (/\b(negative|worst|unhappiest|most dissatisfied|most complaints|critical|unhappy)\b/i.test(lastUser)) {
    const topNegative = [...themes].sort((a, b) => b.negative_pct - a.negative_pct).slice(0, 3);
    if (topNegative.length === 0) {
      return {
        reply: 'No theme data is loaded right now, so I cannot rank negative themes yet.',
        sources: ['summary'],
        clusterId: null
      };
    }

    return {
      reply:
        'Most negative themes:\n' +
        topNegative
          .map((theme, index) => `${index + 1}. ${theme.name} (${theme.negative_pct}% negative, ${theme.volume.toLocaleString()} entries)`)
          .join('\n') +
        `\n${topNegative[0].name} is the loudest pain point in the dashboard.`,
      sources: topNegative.map((theme) => `cluster:${theme.cluster_id}`),
      clusterId: topNegative[0].cluster_id
    };
  }

  if (/\b(roadmap|planned|backlog|under review|active item|initiative)\b/i.test(lastUser)) {
    const grouped = {
      Active: roadmapItems.filter((item) => item.status === 'Active'),
      Planned: roadmapItems.filter((item) => item.status === 'Planned'),
      'Under Review': roadmapItems.filter((item) => item.status === 'Under Review'),
      Backlog: roadmapItems.filter((item) => item.status === 'Backlog')
    };

    return {
      reply:
        'Roadmap status across linked themes:\n' +
        [
          `- Active: ${grouped.Active.length > 0 ? grouped.Active.map((item) => `${item.roadmap_id} ${item.theme_name}`).join(', ') : 'none'}`,
          `- Planned: ${grouped.Planned.length > 0 ? grouped.Planned.map((item) => `${item.roadmap_id} ${item.theme_name}`).join(', ') : 'none'}`,
          `- Under Review: ${grouped['Under Review'].length > 0 ? grouped['Under Review'].map((item) => `${item.roadmap_id} ${item.theme_name}`).join(', ') : 'none'}`,
          `- Backlog: ${grouped.Backlog.length > 0 ? grouped.Backlog.map((item) => `${item.roadmap_id} ${item.theme_name}`).join(', ') : 'none'}`
        ].join('\n'),
      sources: ['roadmap'],
      clusterId: null
    };
  }

  if (/\b(trend|trends|monthly|over time|month-over-month|month over month|growing|declining|trajectory)\b/i.test(lastUser)) {
    if (monthlyTrends.length === 0 || themes.length === 0) {
      return {
        reply: 'No trend data is loaded right now.',
        sources: ['trends'],
        clusterId: null
      };
    }

    const movers = themes
      .map((theme) => ({
        theme,
        peak: peakMonth(theme.cluster_id),
        latest: latestTrend(theme.cluster_id)
      }))
      .sort((a, b) => b.latest.deltaPct - a.latest.deltaPct);

    const riser = movers[0];
    const decliner = [...movers].sort((a, b) => a.latest.deltaPct - b.latest.deltaPct)[0];
    const peakLeader = [...movers].sort((a, b) => b.peak.volume - a.peak.volume)[0];

    return {
      reply:
        `Trend window covers ${monthlyTrends[0].month} through ${monthlyTrends[monthlyTrends.length - 1].month}. ` +
        `${riser.theme.name} has the biggest latest month-over-month increase at ${riser.latest.deltaPct}%, while ${decliner.theme.name} has the weakest latest movement at ${decliner.latest.deltaPct}%. ` +
        `${peakLeader.theme.name} reaches the highest single-month volume with ${peakLeader.peak.volume} mentions in ${peakLeader.peak.month}.`,
      sources: ['trends', `cluster:${riser.theme.cluster_id}`, `cluster:${decliner.theme.cluster_id}`, `cluster:${peakLeader.theme.cluster_id}`],
      clusterId: null
    };
  }

  if (/\b(channel|app review|social media|support ticket|beta test|distribution)\b/i.test(lastUser)) {
    if (channels.length === 0) {
      return {
        reply: 'No channel breakdown is loaded right now.',
        sources: ['channels'],
        clusterId: null
      };
    }

    const channelTotal = channels.reduce((sum, channel) => sum + channel.count, 0);
    const topChannel = [...channels].sort((a, b) => b.count - a.count)[0];

    return {
      reply:
        `Feedback channel mix across ${channelTotal.toLocaleString()} entries:\n` +
        channels.map((channel) => `- ${channel.name}: ${channel.pct}% (${channel.count.toLocaleString()} entries)`).join('\n') +
        `\n${topChannel.name} is the largest source by volume.`,
      sources: ['summary', 'channels'],
      clusterId: null
    };
  }

  if (/\b(recommend|action|next step|suggest|what should we do|prioritize)\b/i.test(lastUser)) {
    const topThree = themesByPriority.slice(0, 3);
    if (topThree.length === 0) {
      return {
        reply: 'No theme data is loaded right now, so I cannot recommend next steps yet.',
        sources: ['summary'],
        clusterId: null
      };
    }

    return {
      reply:
        'Recommended next steps:\n' +
        topThree
          .map((theme, index) => `${index + 1}. ${theme.name} — priority ${theme.priority_score}, ${theme.negative_pct}% negative, ${theme.volume.toLocaleString()} entries`)
          .join('\n') +
        `\nStart with ${topThree.map((theme) => theme.name).join(', then ')}.`,
      sources: topThree.map((theme) => `cluster:${theme.cluster_id}`),
      clusterId: topThree[0].cluster_id
    };
  }

  if (/\b(jira|ticket|draft|create (a )?ticket|write (a )?ticket)\b/i.test(lastUser)) {
    const [mentionedTheme] = detectThemes(lastUser);
    const fallbackTheme = themesByPriority[0];
    if (!fallbackTheme) {
      return {
        reply: 'No theme data is loaded right now, so I cannot build a ticket template yet.',
        sources: ['summary'],
        clusterId: null
      };
    }

    return ticketTemplate(mentionedTheme ?? fallbackTheme.cluster_id);
  }

  return {
    reply:
      'I can answer questions about feedback themes, sentiment, trends, roadmap status, and priorities. ' +
      'Try asking about a theme, active roadmap items, top issues, or a quick project overview.',
    sources: ['summary'],
    clusterId: null
  };
}
