import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-[#00DD55] text-black hover:bg-[#22DD66]",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline:
          "border-2 border-[#00DD55] bg-transparent text-[#00DD55] hover:bg-[#00DD55]/10 hover:border-[#22DD66]",
        secondary:
          "bg-[#00BB44] text-white hover:bg-[#00DD55]",
        ghost: "hover:bg-[#00DD55]/10 text-[#00DD55]",
        link: "text-[#00DD55] underline-offset-4 hover:text-[#22DD66] hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild, children, ...props }, ref) => {
    // Add neon glow for default variant
    const glowStyle = variant === 'default' || variant === undefined
      ? { boxShadow: '0 0 6px #00DD55, 0 0 12px #00BB44, 0 0 20px #22DD66' }
      : variant === 'outline'
      ? { boxShadow: '0 0 6px #00DD55 / 0.3' }
      : undefined

    if (asChild && React.isValidElement(children)) {
      // Clone the child element and apply button styles
      return React.cloneElement(children as React.ReactElement, {
        className: cn(buttonVariants({ variant, size, className }), children.props.className),
        style: { ...children.props.style, ...glowStyle },
        ref,
        ...props,
        // Remove asChild from props to prevent it from being passed to DOM
        asChild: undefined,
      })
    }
    
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        style={glowStyle}
        ref={ref}
        {...props}
      >
        {children}
      </button>
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }

