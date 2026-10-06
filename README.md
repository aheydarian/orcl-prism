# orcl-prism

Interactive 3D header for the ORCL website (Omni-Reality & Cognition Lab, University of Virginia): a person in a VR headset who looks from screen to screen inside a glass orb, circled by the lab's ten research projects.

- Full page (a stand-alone copy of the lab's UVA home page, with the animation where the banner photo is): https://aheydarian.github.io/orcl-prism/
- Animation only, to sit where the banner photo is on the lab's UVA home page: https://aheydarian.github.io/orcl-prism/#media
- Whole banner (title, text, links and animation), if the banner itself has to be replaced: https://aheydarian.github.io/orcl-prism/#embed

## Embedding on the UVA Engineering site

Option A, if the banner's image slot can take embed code: put this in place of the photo.

```html
<iframe src="https://aheydarian.github.io/orcl-prism/#media" title="ORCL research projects (interactive)" loading="lazy"
  style="display:block;width:100%;aspect-ratio:670/507;height:auto;border:1px solid #E57200;background:#141E3C;position:relative"></iframe>
```

Option B, if the banner only takes an image: replace the banner with an unrestricted source code section that holds the banner's own markup, with the iframe where the image was.

```html
<div class="unit_feature">
  <div class="fs-row">
    <div class="fs-cell">
      <div class="unit_feature_inner">
        <figure class="unit_feature_figure">
          <iframe src="https://aheydarian.github.io/orcl-prism/#media" title="ORCL research projects (interactive)" loading="lazy"
            style="display:block;width:100%;aspect-ratio:670/507;height:auto;border:1px solid #E57200;background:#141E3C;position:relative"></iframe>
        </figure>
        <div class="unit_feature_wrapper">
          <h1 class="unit_feature_title">Where Virtual Worlds Meet Human Behavior</h1>
          <span class="unit_feature_description"><p>The Omni-Reality &amp; Cognition Lab builds virtual, augmented and mixed reality simulators, instruments them with eye tracking and physiological sensing, and uses them to design safer streets, healthier buildings and better training for high-stakes work.</p></span>
          <div class="unit_feature_links">
            <a href="/labs-groups/omni-reality-cognition-lab/research" class="unit_feature_link" aria-label="Visit Explore our research"><span class="unit_feature_link_inner"><span class="unit_feature_link_label">Explore our research</span> <span class="icon_nowrap unit_feature_link_icon" aria-hidden="true"><svg class="icon icon_arrow_right"><use xlink:href="/themes/custom/uvae/frontend/static-html/images/icons.svg#arrow_right"></use></svg></span></span></a>
            <a href="/labs-groups/omni-reality-cognition-lab/who-we-are" class="unit_feature_link" aria-label="Visit Meet the team"><span class="unit_feature_link_inner"><span class="unit_feature_link_label">Meet the team</span> <span class="icon_nowrap unit_feature_link_icon" aria-hidden="true"><svg class="icon icon_arrow_right"><use xlink:href="/themes/custom/uvae/frontend/static-html/images/icons.svg#arrow_right"></use></svg></span></span></a>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

The animation sits on UVA navy. For the lighter Sand background from the lab palette instead, use `https://aheydarian.github.io/orcl-prism/#media,bg=sand` as the src and `background:#E9C9A5` on the iframe.

Notes: `position:relative` keeps the page's thin vertical grid rule from drawing over the iframe. The animation pauses itself when scrolled out of view, has a pause button, starts paused for visitors who ask for reduced motion, and shows a still image if WebGL is not available.

## Upcoming Events on the full page

The events list mirrors the "Upcoming Events" block on the lab's UVA page, so events are still added and edited in Drupal as usual.

- `update_events.py` reads that block and writes `events.json`. `.github/workflows/update-events.yml` runs it once a day, at 4:37 am Pacific (7:37 am Eastern) during daylight time, and commits `events.json` when the list changes. GitHub Pages then republishes the site. To run it right away, open the Actions tab, choose "Update events" and press "Run workflow".
- The page loads `events.json` each time it opens and hides events that have ended, even between refreshes. With no upcoming events it says so.
- Status, Oct 6, 2026: engineering.virginia.edu sits behind Cloudflare, which answers the workflow with 403 Forbidden. The run then logs a warning and keeps the current list. It will start updating, with no changes here, once UVA web services allow requests with the user agent `ORCL-events-updater` to `/labs-groups/omni-reality-cognition-lab`. Until then, update `events.json` by hand: edit it on GitHub, or save the lab page from a browser and run `python update_events.py --html saved-page.html`.
- Any other fetch error fails the run, keeps the last good list, and GitHub notifies the repository owner.
- GitHub pauses scheduled workflows in a public repository after 60 days without activity. If the repository has had no commit for 50 days, the workflow makes an empty commit to keep itself running.
