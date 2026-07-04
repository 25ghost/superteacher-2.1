export const seedLetters = [
  {
    id: "demo-montmartre",
    title: "The Blue Stairwell",
    locationName: "Montmartre, Paris",
    lat: 48.8867,
    lng: 2.3431,
    dateString: "April 17, 1989",
    textContent:
      "I left the key under the third blue tile because I wanted you to know I had not forgotten the sound of your shoes in the stairwell. If you find this, do not knock. Listen first.",
    portraitUrl: "/assets/references/aged-script.png",
    audioUrl: "",
    secretClueTags: ["blue tile", "stairwell", "key"],
    createdAt: null,
  },
  {
    id: "demo-kigali",
    title: "Rain on the Tin Roof",
    locationName: "Nyamirambo, Kigali",
    lat: -1.9706,
    lng: 30.1044,
    dateString: "November 3, 2007",
    textContent:
      "The rain made a drum of the whole roof that night. I wrote your name in the fogged window and wiped it away before anyone woke. Some names are safest as weather.",
    portraitUrl: "/assets/references/stationery-light.png",
    audioUrl: "",
    secretClueTags: ["rain", "window", "tin"],
    createdAt: null,
  },
  {
    id: "demo-reykjavik",
    title: "Ash Map",
    locationName: "Reykjavik, Iceland",
    lat: 64.1466,
    lng: -21.9426,
    dateString: "June 22, 1975",
    textContent:
      "The map was wrong, but the ash knew where to settle. I followed the coast until every black stone looked like a sealed envelope.",
    portraitUrl: "/assets/references/polar-map.png",
    audioUrl: "",
    secretClueTags: ["ash", "coast", "sealed"],
    createdAt: null,
  },
  {
    id: "demo-kyoto",
    title: "Paper Lantern Hour",
    locationName: "Gion, Kyoto",
    lat: 35.0037,
    lng: 135.7788,
    dateString: "September 9, 1996",
    textContent:
      "At lantern hour the alley became a throat of gold. I carried your letter for six blocks and still could not decide whether delivering it was mercy.",
    portraitUrl: "/assets/references/wax-seal.png",
    audioUrl: "",
    secretClueTags: ["lantern", "gold", "mercy"],
    createdAt: null,
  },
];

export const seedEchoes = [
  {
    id: "echo-1",
    letterId: "demo-montmartre",
    authorName: "Someone passing through",
    textContent: "I knew a blue stairwell once. It kept every goodbye louder than the door.",
    type: "reply",
    lat: 48.86,
    lng: 2.34,
    createdAt: null,
  },
  {
    id: "echo-2",
    letterId: "demo-kigali",
    authorName: "Anonymous",
    textContent: "I still write names on glass and pretend the rain is the one confessing.",
    type: "independent_confession",
    lat: -1.96,
    lng: 30.08,
    createdAt: null,
  },
];

