import { describe, it, expect } from "vitest";

import { mount } from "@vue/test-utils";
import NavItem from "../NavItem.vue";

describe("NavItem", () => {
  it("renders properly", () => {
    const wrapper = mount(NavItem, {
      props: {
        to: {
          name: "test-view",
        },
      },
      slots: {
        default: "Test View",
      },
    });
    expect(wrapper.text()).toContain("Test View");
  });
});
