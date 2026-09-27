import { type Activity, type ActivityContext, defineActivity } from "../../activity";
import { galleryView } from "./gallery-view";

export interface GalleryInput {
  readonly source: "shell-navigation";
}

class GalleryActivity implements Activity<GalleryInput, never> {
  initialize(_input: GalleryInput, _context: ActivityContext<never>): void {}

  render(): unknown {
    return galleryView();
  }
}

export const galleryActivity = defineActivity<GalleryInput, never>({
  key: "component-gallery",
  shellProfile: "workspace",
  create: () => new GalleryActivity(),
});
