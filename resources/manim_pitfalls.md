# Manim Pitfalls

This document collects all of the stumbling blocks I've encountered trying to create complex animations with manim.

## Unintuitive

### .animate.rotate()

This doesn't do what you would hope it would do. Use `Rotate(object)` instead.

See [Reference - `.animate`](#animate).
`.animate` just linearly interpolates from the initial to the final mobject.
A rotation is critically *not* a linear interpolation.

### Opacity is separate from color

I've gotten caught out a couple times forgetting that
you need to set opacity via fully separate vars from color,
despite the fact that ManimColor supports an opacity.

I think this is a good design decision,
it's just a little confusing from the type hinting and method docs
not particularly doing a lot to point out the distinction.

### Differences between Text and Tex

-   `font_size` on Text seems 1.5x larger than the same value on Tex
-   if color and stroke_color are set, but not fill_color:
    -   for Text, you get stroke_color as stroke and color as fill (good)
    -   for Tex, you get stroke_color as stroke *and* fill (weird)

## Limitations

### Simultaneous Animations

Manim often does not achieve intended results when trying to run two simultaneous animations. Particularly, do not combine:

-   Two Animations controlling the same property
-   An `.animate` and any other animation.
    -   [`.animate`](#animate) uses a `MoveToTarget` animation, which linearly interpolates *all* of an object's properties, including other properties you're trying to animate.

### Elements with no points?

When animating Text and Tex objects,
if I want to Transform() to a state with no points (e.g. ""),
that animation slides the points of the text from its position to the **origin**,
instead of collapsing the points at the Text's location.
I suspect this is because Mobjects use their points as the authoritative position, instead of storing some inner position to draw around?

### Text alignment

Related to the above,
if you transform one text with a bunch of high-reaching characters e.g. "PTWY"
into a text with a bunch of low-reaching characters e.g. "gpqy",
the characters do not stay aligned to a baseline, instead shifting upwards.
The same thing happens if you try to align two different Tex(t) objects -
their position isn't indicative of the letter baseline,
only the center of mass of the points,
so they'll be offset from each other.

### Adding new elements to Groups in a scene

If you want to do a draw-in animation for new elements in a scene,
and also have them be part of a group,
the right sequence would be:

1.  Instantiate new elements
2.  Animate the elements being added to the scene
3.  Add them to any Groups you want

If you add elements to a Group which is already part of a scene,
they will instantly start rendering in the scene,
so you lose the chance to animate their creation.

This makes it more complicated to create new group elements
*while* that group is being animated.
I imagine you could get this working with temporary updaters
on the new elements while they're being created,
then replace the updaters with group membership afterwards,
but it's finicky.
You could also maybe instantiate elements as transparent,
then add them to the group,
then animate their "creation" by switching color from transparent
to your desired color?
This wouldn't immediatley do the same thing,
it wouldn't sweep through the object's points like Create() normally does,
but maybe it's a start?

### Gradients

TODO: clean up

-   setting opacity and color is different, despite color having an opacity
-   type annotations for set_color and set_opacity say single types, but the methods allow lists
    -   they also seem to apply backwards from the start to the end of the points?
-   only linear gradient, no other forms. sheen is hard to figure out, under-documented.

## Bugs

## Circle.point_at_angle

After a rotation or reflection which moves a Circle's starting point away from the RIGHT axis, Circle.point_at_angle() returns incorrect results.

Reported to ManimCommunity in [github.com/ManimCommunity issue #4236](https://github.com/ManimCommunity/manim/issues/4236)

## Reference

Extra details and further info in support of the above.

### .animate

Internallly, `.animate` just applies all of the modifications to a `target` copy of the object,
and runs a `MoveToTarget` animation from the src to the `target`,
which just linearly interpolates all of the properties of the Mobject from src to target -
color, stroke_width, and most importantly, all the individual points.
