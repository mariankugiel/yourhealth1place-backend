type ToastProps = {
  title: string
  description: string
  duration?: number
}

export function toast({ title, description, duration = 3000 }: ToastProps) {
  // Create a toast element
  const toastElement = document.createElement("div")
  toastElement.className =
    "fixed top-4 right-4 z-50 max-w-md bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 transition-all duration-300 transform translate-y-0 opacity-0"

  // Create toast content
  const toastContent = document.createElement("div")
  toastContent.className = "flex flex-col gap-1"

  // Create title
  const titleElement = document.createElement("div")
  titleElement.className = "font-medium text-gray-900 dark:text-gray-100"
  titleElement.textContent = title

  // Create description
  const descriptionElement = document.createElement("div")
  descriptionElement.className = "text-sm text-gray-500 dark:text-gray-400"
  descriptionElement.textContent = description

  // Append elements
  toastContent.appendChild(titleElement)
  toastContent.appendChild(descriptionElement)
  toastElement.appendChild(toastContent)

  // Append to body
  document.body.appendChild(toastElement)

  // Animate in
  setTimeout(() => {
    toastElement.classList.remove("opacity-0")
    toastElement.classList.add("opacity-100")
  }, 10)

  // Remove after duration
  setTimeout(() => {
    toastElement.classList.remove("opacity-100")
    toastElement.classList.add("opacity-0")

    // Remove from DOM after animation
    setTimeout(() => {
      document.body.removeChild(toastElement)
    }, 300)
  }, duration)
}
