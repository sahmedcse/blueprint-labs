import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { WaitlistForm } from "./waitlist-form";

describe("WaitlistForm", () => {
  it("shows an error and does not submit an invalid email", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<WaitlistForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Email"), "not-an-email");
    await user.click(screen.getByRole("button", { name: "Join the waitlist" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Enter a valid email address",
    );
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits a valid email", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<WaitlistForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.click(screen.getByRole("button", { name: "Join the waitlist" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit.mock.calls[0][0]).toEqual({ email: "ada@example.com" });
  });
});
