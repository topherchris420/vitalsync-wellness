import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const html = await readFile(new URL('../index.html', import.meta.url), 'utf8');

test('landing page exposes premium wellness positioning and metadata', () => {
  assert.match(html, /<title>VitalSync Wellness - Sync Your Daily Wellness Rhythm<\/title>/);
  assert.match(
    html,
    /VitalSync Wellness helps you track habits, mood, recovery, and daily routines to reveal personal wellness patterns and support healthier decisions\./,
  );
  assert.match(html, /property="og:title"/);
  assert.match(html, /name="twitter:card"/);
  assert.match(html, /Sync your daily wellness into one clear rhythm\./);
});

test('landing page includes the expected conversion and trust sections', () => {
  for (const id of [
    'hero',
    'how-it-works',
    'features',
    'trust',
    'founder',
    'final-cta',
    'chat',
  ]) {
    assert.match(html, new RegExp(`<section[^>]+id="${id}"`));
  }

  for (const phrase of [
    'Track your daily signals',
    'Discover your patterns',
    'Build a healthier rhythm',
    'Mood and energy tracking',
    'Habit and routine syncing',
    'Recovery and sleep awareness',
    'Personalized wellness insights',
    'Progress trends',
    'Calm daily check-ins',
    'privacy-first wellness tracking',
  ]) {
    assert.match(html, new RegExp(phrase));
  }
});

test('landing page keeps clear general wellness boundaries', () => {
  assert.match(
    html,
    /VitalSync Wellness is designed for general wellness support and is not a medical device or a substitute for professional medical advice\./,
  );
  assert.match(html, /not a substitute for medical care/i);
});
test('inline application script compiles', () => {
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((match) => match[1]);
  assert.ok(scripts.length > 0, 'expected at least one inline script');

  for (const script of scripts) {
    assert.doesNotThrow(() => new Function(script));
  }
});