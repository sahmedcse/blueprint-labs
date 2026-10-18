"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";

// The schema is the single source for validation and for the form's types.
export const waitlistSchema = z.object({
  email: z.email("Enter a valid email address"),
});

export type WaitlistValues = z.infer<typeof waitlistSchema>;

type WaitlistFormProps = {
  onSubmit: (values: WaitlistValues) => void | Promise<void>;
};

export function WaitlistForm({ onSubmit }: WaitlistFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<WaitlistValues>({
    resolver: zodResolver(waitlistSchema),
    defaultValues: { email: "" },
  });

  return (
    <form
      noValidate
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-col gap-2"
    >
      <label htmlFor="waitlist-email" className="text-sm font-medium">
        Email
      </label>
      <div className="flex gap-2">
        <input
          id="waitlist-email"
          type="email"
          autoComplete="email"
          aria-invalid={errors.email ? true : undefined}
          aria-describedby={errors.email ? "waitlist-email-error" : undefined}
          className="h-9 flex-1 rounded-md border border-input bg-background px-3 text-sm outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 aria-invalid:border-destructive"
          {...register("email")}
        />
        <Button type="submit" disabled={isSubmitting}>
          Join the waitlist
        </Button>
      </div>
      {errors.email ? (
        <p id="waitlist-email-error" role="alert" className="text-sm text-destructive">
          {errors.email.message}
        </p>
      ) : null}
    </form>
  );
}
