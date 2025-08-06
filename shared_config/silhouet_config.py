# silhouet_config.py

# Define your comprehensive list of personality keys.
# This list must be identical and ordered consistently across all services
# that refer to personality scores.
PERSONALITY_KEYS = [
    "intellectual_honesty",
    "courage",
    "nobility",
    "self_respect",
    "empathy",
    "aggression",
    "resentment",
    "idealism",
    "cynicism",
    "loneliness",
    "creativity",
    "frustration",
    "conformity_pressure",
    "tribal_affiliation",
    "curiosity",
    "innovation_optimism",
    "self_worth",
    "willingness_conspiracy_theories",
    "emotional_state_anxiety",
    "emotional_state_sadness",
    "emotional_state_anger",
    "attachment_needs",
    "self_loathing",
    "pride",
    "relationship_satisfaction",
    "desire_for_connection",
    "ambition_motivation",
    "gratitude",
    "entitlement",
    "fear_of_judgment",
    "confidence_in_future_self",
    "shame",
    "guilt",
    "trust_in_institutions",
    "perception_of_justice",
    "moral_alignment_with_society",
    "dissatisfaction_with_culture_media",
    "concern_over_decline_collapse",
    "political_engagement_level",
    "faith_in_democracy",
    "sense_of_alienation",
    "systemic_paranoia",
    "preference_for_strong_leadership_vs_consensus",
    "libertarianism_vs_collectivism",
    "tolerance_for_authority",
    "openness_to_change_reform",
    "compliance_sentiment",
    "views_on_taxation",
    "polarization_intensity",
    "willingness_to_protest_or_comply",
    "brand_loyalty",
    "frustration_with_products",
    "openness_to_alternatives",
    "cost_sensitivity",
    "trust_in_advertising",
    "expectations_from_businesses",
    "belief_in_capitalism",
    "personal_financial_satisfaction"
]

# Aggregation frequencies in hours (can be loaded from environment variables)
AGGREGATION_FREQUENCIES = {
    "pincode": 1,
    "district": 2,
    "state": 4,
    "country": 6,
    "world": 24,
}

PERSONALITY_LABEL_MAP = {
  "intellectual_honesty": [
    "I could be wrong, and I want to hear the other side.",
    "I already know I'm right, people just don't get it."
  ],
  "courage": [
    "Even if it costs me, I have to speak the truth.",
    "I stay quiet; what's the point in standing up?"
  ],
  "nobility": [
    "Some things are worth doing even if no one sees them.",
    "Why bother helping if no one notices or cares?"
  ],
  "self_respect": [
    "I demand to be treated with dignity and respect.",
    "I have a hard time standing up for myself and often let people walk all over me."
  ],
  "empathy": [
    "I can imagine how hard that must be for them.",
    "People just need to stop being so sensitive."
  ],
  "aggression": [
    "I don't back down, and I hit back harder.",
    "I don't get into fights; it's not worth it."
  ],
  "resentment": [
    "People like them always get ahead while I’m stuck.",
    "I'm happy when others succeed; it's not a competition."
  ],
  "idealism": [
    "We have to believe the world can be better.",
    "That's just how things are, no use dreaming."
  ],
  "cynicism": [
    "You can't trust anyone; everyone has a hidden agenda.",
    "I believe in people's good intentions and their ability to help one another."
  ],
  "loneliness": [
    "No one really sees me—I’m just here.",
    "I feel connected, like I belong somewhere."
  ],
  "creativity": [
    "What if we tried something completely new?",
    "Let's just stick to what already works."
  ],
  "frustration": [
    "I'm so fed up; I feel like I'm hitting my head against a wall.",
    "I feel a sense of calm and acceptance about how things are."
  ],
  "conformity_pressure": [
    "I can't say what I really think, because it won't be accepted.",
    "I speak my mind, even if it’s unpopular."
  ],
  "tribal_affiliation": [
    "We have to defend our group - outsiders don't understand.",
    "I care about ideas, not which side they come from."
  ],
  "curiosity": [
    "I want to know how and why everything works.",
    "I don't think about that stuff - it's not interesting."
  ],
  "innovation_optimism": [
    "Technology can solve more than we give it credit for.",
    "We're just creating more problems with this progress."
  ],
  "self_worth": [
    "I matter, even if no one tells me that.",
    "I don't think I bring much value to anything."
  ],
  "willingness_conspiracy_theories": [
    "I believe there is a secret group that controls the world's events.",
    "I am skeptical of elaborate stories and prefer to stick to verifiable facts."
  ],
  "emotional_state_anxiety": [
    "I can't stop thinking about everything that could go wrong.",
    "I feel grounded and at ease right now."
  ],
  "emotional_state_sadness": [
    "Lately, it feels like the joy is just not there.",
    "Things feel light and I'm genuinely content."
  ],
  "emotional_state_anger": [
    "I'm sick of being ignored and treated like this.",
    "I feel peaceful - it's not worth getting angry."
  ],
  "attachment_needs": [
    "I just want someone to really stay close.",
    "I'm fine on my own - I don't need anyone."
  ],
  "self_loathing": [
    "I hate who I’ve become.",
    "I accept myself, flaws and all."
  ],
  "pride": [
    "I'm proud of what I've overcome.",
    "There's nothing special about what I've done."
  ],
  "relationship_satisfaction": [
    "I feel safe and understood with them.",
    "We're just going through the motions - it's empty."
  ],
  "desire_for_connection": [
    "I wish I had someone to really talk to.",
    "I need space, I am better alone."
  ],
  "ambition_motivation": [
    "I am pushing myself because I know I can do more.",
    "I can't find the drive to start anything anymore."
  ],
  "gratitude": [
    "I am lucky to have what I do.",
    "I deserve more than what I've been given."
  ],
  "entitlement": [
    "People owe me for everything I've put up with.",
    "No one owes me anything - I earn what I get."
  ],
  "fear_of_judgment": [
    "If I show the real me, they'll tear me down.",
    "Let them judge, I'm not changing for anyone."
  ],
  "confidence_in_future_self": [
    "I believe I'll handle whatever comes my way.",
    "I don't trust myself to figure anything out."
  ],
  "shame": [
    "I feel like I'll never live this down.",
    "I'm not ashamed—I did what I had to."
  ],
  "guilt": [
    "It eats at me - I messed up and hurt them.",
    "I did my best - I don't feel guilty about it."
  ],
  "trust_in_institutions": [
    "I still believe the system can work.",
    "They're all corrupt - none of it can be trusted."
  ],
  "perception_of_justice": [
    "Sometimes justice actually happens—it gives me hope.",
    "It's always the powerful who get away with it."
  ],
  "moral_alignment_with_society": [
    "I feel like my values mostly match what’s around me.",
    "I don't belong in this culture - it's broken."
  ],
  "dissatisfaction_with_culture_media": [
    "Everything feels fake and superficial lately.",
    "I enjoy a lot of what’s out there right now."
  ],
  "concern_over_decline_collapse": [
    "Feels like the whole system's coming apart.",
    "We have been through worse - it'll work itself out."
  ],
  "political_engagement_level": [
    "I read, vote, and try to stay involved.",
    "I don't follow politics - it's all noise."
  ],
  "faith_in_democracy": [
    "Democracy's messy, but it's still worth defending.",
    "Voting doesn't matter - it's all rigged anyway."
  ],
  "sense_of_alienation": [
    "I don't feel connected to anyone around me.",
    "I feel like I'm part of something bigger."
  ],
  "systemic_paranoia": [
    "They're watching, manipulating - nothing's accidental.",
    "Most things are just incompetence, not conspiracy."
  ],
  "preference_for_strong_leadership_vs_consensus": [
    "We need someone decisive who doesn't ask permission.",
    "Leaders should listen and bring people together."
  ],
  "libertarianism_vs_collectivism": [
    "Just leave people alone and let them choose.",
    "We need more collective support and shared responsibility."
  ],
  "tolerance_for_authority": [
    "Rules are there for a reason - follow them.",
    "Authority should always be questioned - it's dangerous."
  ],
  "openness_to_change_reform": [
    "Things need to evolve - we can't stay stuck.",
    "Changing things now will just make it worse."
  ],
  "compliance_sentiment": [
    "I usually follow the rules without question.",
    "I don't comply just because someone said to."
  ],
  "views_on_taxation": [
    "Taxes help hold society together - it's worth it.",
    "Why should I pay for things I don't use?"
  ],
  "polarization_intensity": [
    "You're either with us or against us.",
    "People can disagree and still be decent."
  ],
  "willingness_to_protest_or_comply": [
    "If something's wrong, I'll be out there protesting.",
    "I keep my head down - it's safer that way."
  ],
  "brand_loyalty": [
    "I always stick to the brands I trust.",
    "I'll switch to whatever works better or cheaper."
  ],
  "frustration_with_products": [
    "Why is everything so buggy and broken?",
    "Stuff just works - I rarely have issues."
  ],
  "openness_to_alternatives": [
    "I am eager to explore different products and alternative solutions.",
    "I am wary of change and prefer to stick with what is familiar and proven."
  ],
  "cost_sensitivity": [
    "If it's not on sale, I won't buy it.",
    "I don't mind paying more if it saves time."
  ],
  "trust_in_advertising": [
    "Sometimes the ads are actually right.",
    "They'll say anything to sell; it's all manipulation."
  ],
  "expectations_from_businesses": [
    "I expect companies to act responsibly.",
    "It's just business, they don;t owe anyone anything."
  ],
  "belief_in_capitalism": [
    "Capitalism's messy, but it’s the best we’ve got.",
    "The system's rigged—it only helps the powerful."
  ],
  "personal_financial_satisfaction": [
    "I feel stable and in control of my finances.",
    "I'm constantly stressed about money."
  ]
}
