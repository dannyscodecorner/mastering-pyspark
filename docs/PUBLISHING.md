# Publishing the course

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

## Publishing the lab

The slides' **Download the lab** link downloads `pyspark-labs.zip` from the latest GitHub Release. The ZIP is a release attachment, not a committed file or part of the Pages build.

1. Commit and validate the intended lab changes. Prepare the ZIP from a checkout matching the release tag, including the prepared data and `uv.lock`.
2. From that checkout's repository root, run:

   ```text
   python3 labs/author/package_lab.py
   ```

   This creates `.build/releases/pyspark-labs.zip`. It excludes local environments, caches and run output. No Spark or Incan installation is needed to package the files.

3. Create a draft [GitHub Release](https://github.com/dannyscodecorner/mastering-pyspark/releases) for the tag and attach the ZIP with the exact name `pyspark-labs.zip`.
4. Check the attachment extracts into a complete `labs` folder, then publish the release and mark it as the latest release. Use a regular release, not a prerelease.

Every release marked as latest must include that attachment. The download link will not work until the first release with the attachment is published. Publishing Pages does not create or update a release.

GitHub documents the stable [`releases/latest/download/asset-name.zip` URL](https://docs.github.com/en/repositories/releasing-projects-on-github/linking-to-releases#linking-to-the-latest-release). Keep the asset name unchanged so the slide link follows new releases automatically.

## Pages settings

Under **Settings → Pages**, the publishing source is **Deploy from a branch**, with **gh-pages** and **/ (root)** selected. HTTPS is enabled. No custom domain is configured.

The generated site uses relative links so its browser assets and lab walkthrough work under the `/mastering-pyspark/` project path. The lab ZIP downloads directly from GitHub Releases. URLs can link directly to a slide, for example [Structured Streaming](https://dannyscodecorner.github.io/mastering-pyspark/#section-7).

See GitHub's [publishing-source documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) for the branch publishing mechanism.
