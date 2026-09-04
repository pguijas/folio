# PageFeedback

A "Was this page helpful?" widget with thumbs up/down buttons. After clicking, the widget displays a confirmation message and stores the response in the browser's `localStorage` under the key `page-feedback`, keyed by page path.

This component is used internally by the theme layout and is typically placed at the bottom of documentation pages. It takes no props.

## API

### PageFeedback

This component takes no props.

**Behavior:**
- Displays thumbs up/down buttons
- On click, shows "Glad it helped!" or "Thanks, we'll improve this page."
- Feedback is stored per-page in `localStorage` and cannot be resubmitted (until `localStorage` is cleared)

## Example

<PreviewCode>

```mdx
<PageFeedback />
```

<Callout type="info" title="Layout Component">
  PageFeedback is rendered at the bottom of every documentation page by the theme layout. Scroll to the bottom of this page to see the "Was this helpful?" widget in action.
</Callout>

</PreviewCode>
