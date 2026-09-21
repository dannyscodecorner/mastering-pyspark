# Publishing the slides

The presentation is hosted at [dannyscodecorner.github.io/mastering-pyspark](https://dannyscodecorner.github.io/mastering-pyspark/).

The `main` branch contains the Incan sources and lab project. The `gh-pages` branch contains only the generated website: slides, browser assets, reference decks and the linked lab material. GitHub Pages publishes that branch's root. The `.nojekyll` file keeps these prebuilt files out of Jekyll processing.

## Publish an update

From the repository root, with Incan installed and Git authenticated for this repository:

1. Commit the intended slide, lab and tooling changes to `main`, and push them.
2. Build and verify the website:

   ```text
   python3 tools/course.py build
   python3 tools/course.py verify
   ```

3. Review the local presentation with `python3 tools/course.py serve`.
4. Prepare the publication, then publish it:

   ```text
   python3 tools/publish_pages.py --dry-run
   python3 tools/publish_pages.py
   ```

5. Wait for the **pages build and deployment** run in [GitHub Actions](https://github.com/dannyscodecorner/mastering-pyspark/actions) to succeed, then check the public slides and their lab links.

The publishing command requires a current verified build and committed build inputs. It uses a temporary checkout, retains the publication history and pushes without force. It does not stage or commit files in your source checkout. An unchanged website produces no new deployment commit.

Publication is explicit: building locally or pushing `main` alone does not deploy the slides. Incan runs locally; visitors need only a browser. The lab download still runs on the attendee's machine.

## Pages settings

Under **Settings → Pages**, the publishing source is **Deploy from a branch**, with **gh-pages** and **/ (root)** selected. HTTPS is enabled. No custom domain is configured.

The generated site uses relative links so its assets and downloads work under the `/mastering-pyspark/` project path. URLs can link directly to a slide, for example [Structured Streaming](https://dannyscodecorner.github.io/mastering-pyspark/#section-7).

See GitHub's [publishing-source documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) for the branch publishing mechanism.
