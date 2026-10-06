# orcl-prism

Interactive 3D header for the ORCL website (Omni-Reality & Cognition Lab, University of Virginia): a person in a VR headset who looks from screen to screen inside a glass orb, circled by the lab's ten research projects.

- Full page (a stand-alone copy of the lab's UVA home page, with the animation where the banner photo is): https://aheydarian.github.io/orcl-prism/
- Animation only, to sit where the banner photo is on the lab's UVA home page: https://aheydarian.github.io/orcl-prism/#media
- Whole banner (title, text, links and animation), if the banner itself has to be replaced: https://aheydarian.github.io/orcl-prism/#embed

## Embedding on the UVA Engineering site

Option A, if the banner's image slot can take embed code: put this in place of the photo.

```html
<iframe src="https://aheydarian.github.io/orcl-prism/#media" title="ORCL research projects (interactive)" loading="lazy"
  style="display:block;width:100%;aspect-ratio:670/507;height:auto;border:1px solid #E57200;background:#E9C9A5;position:relative"></iframe>
```

Option B, if the banner only takes an image: replace the banner with an unrestricted source code section that holds the banner's own markup, with the iframe where the image was.

```html
<div class="unit_feature">
  <div class="fs-row">
    <div class="fs-cell">
      <div class="unit_feature_inner">
        <figure class="unit_feature_figure">
          <iframe src="https://aheydarian.github.io/orcl-prism/#media" title="ORCL research projects (interactive)" loading="lazy"
            style="display:block;width:100%;aspect-ratio:670/507;height:auto;border:1px solid #E57200;background:#E9C9A5;position:relative"></iframe>
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

The animation sits on Sand (#E9C9A5) from the lab palette. For UVA navy instead, use `https://aheydarian.github.io/orcl-prism/#media,bg=navy` as the src and `background:#141E3C` on the iframe.

Notes: `position:relative` keeps the page's thin vertical grid rule from drawing over the iframe. The animation pauses itself when scrolled out of view, has a pause button, starts paused for visitors who ask for reduced motion, and shows a still image if WebGL is not available.
