/**
 * Built-in default splash-card photo + copy for each watershed, shown on the
 * /path splash page (HomePage) and used as the editable defaults in the admin
 * console (AdminPhotosPage → Splash tab).
 *
 * An admin can override any of these per-watershed via
 * gold.watershed_splash (GET /sites/{watershed} returns splash_* fields);
 * when no override exists the public page and the editor fall back to these.
 */

// Real watershed photos from Unsplash (free for commercial use).
export const SPLASH_PHOTOS: Record<string, string> = {
  mckenzie: 'https://images.unsplash.com/photo-1660806739398-0f0627930230?w=900&h=600&fit=crop', // Tamolitch Blue Pool, McKenzie River OR
  deschutes: 'https://images.unsplash.com/photo-1528672903139-6a4496639a68?w=900&h=600&fit=crop', // Smith Rock / Crooked River canyon (Deschutes tributary) by Dale Nibbe
  metolius: 'https://images.unsplash.com/photo-1657215223750-c4988d4a2635?w=900&h=600&fit=crop', // Cabin on Metolius River, Camp Sherman OR by Lance Reis
  klamath: 'https://images.unsplash.com/photo-1566126157268-bd7167924841?w=900&h=600&fit=crop', // Wood River meandering into Klamath Lake, Chiloquin OR by Dan Meyers
  johnday: 'https://images.unsplash.com/photo-1559867243-edf5915deaa7?w=900&h=600&fit=crop', // Painted Hills, John Day Fossil Beds National Monument OR by Dan Meyers
  skagit: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=900&h=600&fit=crop',
  green_river: 'https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=900&h=400&fit=crop',
  shenandoah: 'https://images.unsplash.com/photo-1697028262529-74efa0627a02?w=900&h=600&fit=crop', // Blue Ridge / Shenandoah valley overlook
  mad_river_oh: 'https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=900&h=600&fit=crop', // spring-fed forested stream — Mad River OH
  ipswich_river_ma: 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=900&h=600&fit=crop', // v0 placeholder (forested river/marsh) — needs Ipswich-specific photo
  clinch_river_va: 'https://images.unsplash.com/photo-1432405972618-c60b0225b8f9?w=900&h=600&fit=crop', // v0 (Appalachian forested river) — needs Clinch-specific photo
  new_river_va: 'https://images.unsplash.com/photo-1559825481-12a05cc00344?w=900&h=600&fit=crop', // v0 (Appalachian river) — needs New River-specific photo
  chattahoochee: 'https://images.unsplash.com/photo-1697028262529-74efa0627a02?w=900&h=600&fit=crop', // v0 placeholder (Blue Ridge) — needs Chattahoochee-specific photo
  meramec: 'https://images.unsplash.com/photo-1652871572027-d127ca7eab8d?w=900&h=600&fit=crop', // v0 — Ozark forested float-stream stock photo (themed); true Meramec photo welcome
}

export const SPLASH_META: Record<string, { tagline: string; narrative: string }> = {
  mckenzie: {
    tagline: 'Fire, recovery, and the return of salmon',
    narrative: 'In September 2020, the Holiday Farm Fire burned 174,390 acres through the McKenzie corridor. Five years later, the watershed tells a remarkable recovery story: species richness has grown from 1,282 to 3,644 — nearly tripling. Chinook salmon are spawning in reaches that were barren. The river endures.',
  },
  deschutes: {
    tagline: '111 miles of canyon ecology and steelhead runs',
    narrative: 'From the springs above Bend to the canyon at Maupin, the Deschutes flows through one of Oregon\'s most dramatic ecological gradients. Cold-water refuges at the headwaters give way to thermal stress zones in the lower canyon. In 2024, anglers harvested 1,757 steelhead — the strongest run in years.',
  },
  metolius: {
    tagline: 'Spring-fed sanctuary — Oregon\'s purest river',
    narrative: 'The Metolius emerges fully formed from the base of Black Butte, a constant 49°F year-round. This spring-fed system is one of the coldest, most stable rivers in Oregon — a refuge for bull trout, kokanee salmon, and the Oregon spotted frog. It is the benchmark against which other watersheds are measured.',
  },
  klamath: {
    tagline: 'The largest dam removal in American history',
    narrative: 'The 2023-2024 removal of four dams on the Klamath River — the largest such action in US history — opened 400 miles of habitat for salmon returning for the first time in a century. Upper Klamath Lake\'s endangered suckers and the Klamath Tribes\' stewardship story make this one of the most consequential ecological experiments on Earth.',
  },
  johnday: {
    tagline: 'Wild & Scenic through ancient fossil beds',
    narrative: 'The John Day is one of the longest free-flowing rivers in the Pacific Northwest — 284 miles without a dam. It cuts through the Painted Hills and John Day Fossil Beds, where 40-million-year-old ecosystems are preserved in stone. Today it supports wild steelhead and spring Chinook runs through high-desert rangeland, making it one of Oregon\'s most remote and ecologically significant watersheds.',
  },
  skagit: {
    tagline: 'All five salmon species in the shadow of the North Cascades',
    narrative: 'The Skagit is the largest river system flowing into Puget Sound and one of only a handful of rivers in the lower 48 that supports all five species of Pacific salmon. Fed by glaciers in North Cascades National Park, the river draws hundreds of bald eagles each winter to feed on spawned-out chum. Its vast estuary — the Skagit Delta — is critical nursery habitat for juvenile Chinook and a key link in the Puget Sound food web.',
  },
  green_river: {
    tagline: 'Flaming Gorge to Canyonlands — ancient fish in a desert canyon',
    narrative: 'The Green River flows 730 miles from Wyoming\'s Wind River Range through Flaming Gorge, Dinosaur National Monument, Desolation Canyon, and into Canyonlands where it meets the Colorado. It is home to four endangered native fish — Colorado pikeminnow, razorback sucker, bonytail chub, and humpback chub — and the world-famous Green River Formation, where 50-million-year-old fossil fish are preserved in exquisite detail. Below Flaming Gorge Dam, tailwater trout fishing rivals the best in the West.',
  },
  shenandoah: {
    tagline: 'Blue Ridge headwaters, limestone springs, and smallmouth main stem',
    narrative: 'From Blue Ridge headwaters in Virginia to the Potomac confluence at Harpers Ferry, West Virginia, the Shenandoah threads two forks through karst valleys fed by cold limestone springs. The North Fork and South Fork meet at Front Royal and run 55 miles north as one of the East Coast\'s premier smallmouth bass fisheries. Cold-water tributaries like Mossy Creek, Smith Creek, and Passage Creek host special-regulation wild trout — the storied Blue Ridge / Massanutten / Allegheny country that George Washington surveyed.',
  },
  mad_river_oh: {
    tagline: "Ohio's spring-fed brown-trout stream through carbonate country",
    narrative: 'The Mad River rises from cold springs near Campbell Hill — the highest point in Ohio — and runs spring-fed and limestone-influenced through Champaign and Clark counties to meet the Great Miami at Dayton. Glacial-outwash aquifers keep it cold and stable through summer, making it one of only two streams in Ohio that hold stocked brown trout: roughly 11,500 yearlings go in every October. Below Springfield it warms into a smallmouth bass river, and its Ordovician-through-Devonian carbonate bedrock carries a rich Paleozoic fossil record. It is the platform\'s first Midwest watershed.',
  },
  ipswich_river_ma: {
    tagline: 'New England\'s endangered river — smallmouth, herring runs, and a watershed that runs dry',
    narrative: 'The Ipswich River winds some 35 miles from headwaters near Wilmington through the marshes of Middleton, Topsfield, and Hamilton to Plum Island Sound. It is a predominantly freshwater smallmouth-and-largemouth river — with stocked and holdover trout, chain pickerel, and an anadromous river-herring run — but it is best known for what stresses it: heavy municipal groundwater withdrawals supplying roughly 330,000 people, most outside the basin, draw stretches dry each summer and landed it on American Rivers\' Most Endangered Rivers list (#8, 2021). Below the Ipswich Mills head-of-tide dam, the estuary opens into a striped-bass fishery on Ipswich Bay. It is the platform\'s first New England watershed.',
  },
  clinch_river_va: {
    tagline: 'Appalachia\'s rarest river — smallmouth, muskie, and the continent\'s richest mussel fauna',
    narrative: 'The Clinch River flows southwest from headwaters near Tazewell through the limestone valleys and coalfields of southwest Virginia to the Tennessee line near Clinchport. Its warm main stem is a trophy smallmouth-bass, muskellunge, and walleye fishery, while cold tributaries like Big Cedar and Indian creeks hold trout. But the Clinch is globally renowned for what lives beneath the surface — the most diverse and imperiled freshwater-mussel fauna in North America (some 46 species) plus the endemic Clinch dace — making it a top global freshwater-biodiversity hotspot. Both main-stem gauges (Cleveland and Dungannon) report live water temperature. It is the platform\'s first Tennessee-River-basin watershed.',
  },
  new_river_va: {
    tagline: 'One of Earth\'s oldest rivers, flowing north — trophy smallmouth, muskie, and walleye',
    narrative: 'Defying convention, Virginia\'s New River flows NORTH through the Blue Ridge and Valley & Ridge of southwest Virginia — from the North Carolina line near Galax, through Claytor Lake, to the West Virginia line at Glen Lyn. Paradoxically named, it is one of the oldest rivers in North America. A large warm-water river (3,770 mi² at Glen Lyn) and one of the South\'s premier smallmouth-bass fisheries, it also produces trophy muskellunge and walleye, with striped and hybrid striped bass, largemouth, and crappie in Claytor Lake. The 57-mile New River Trail State Park shadows its banks. Its forage base is crayfish, hellgrammites, and baitfish rather than mayfly hatches. No main-stem gauge reports water temperature, so the temperature sub-score shows "no data". It is the platform\'s second Tennessee/Ohio-basin watershed.',
  },
  chattahoochee: {
    tagline: 'An urban tailwater trout river through the heart of Atlanta',
    narrative: 'The Chattahoochee runs from Blue Ridge headwaters near Helen through Lake Sidney Lanier and the Buford Dam tailwater — a cold rainbow and brown trout fishery released from the bottom of the lake — then through metro Atlanta and the Chattahoochee River National Recreation Area toward West Point Lake. It is the first urban and first Southeast-US watershed on the platform: striped and spotted bass in Lanier, tailwater trout below Buford Dam, smallmouth and shoal bass downstream, and the historic Dahlonega Gold Belt on the eastern flank. SAFETY: Buford Dam hydropower releases raise the tailwater several feet within minutes — always check the USACE release schedule before wading.',
  },
  meramec: {
    tagline: 'A free-flowing Ozark smallmouth float stream with a spring-fed trout park',
    narrative: 'The Meramec rises in the Ozark highlands near Salem and runs free for 218 miles — no main-stem dam — through the Steelville float corridor, Meramec and Onondaga Cave state parks, and the St. Louis suburbs to the Mississippi River near Arnold. It is the platform\'s first Missouri and first mid-continent karst watershed: a premier smallmouth-bass float stream with spring-fed rainbow trout at Maramec Spring (one of Missouri\'s four trout parks), cave-riddled dolomite bluffs, and Mississippian crinoid fossils. The Big River tributary carries the Old Lead Belt\'s mining legacy — a Superfund tailings site with a lead/sediment TMDL and a fish-consumption advisory.',
  },
}
