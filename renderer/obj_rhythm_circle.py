

# standard libs

# 3rd party libs
from manim import *
# import numpy as np

# my files
from animations import RippleOut
from utils import callback_add_to_vdict, vector_on_unit_circle_clockwise_from_top

# TODO: make a color with a fade towards the edges

# sketch, elements:
# 1. winding arm
# 2. TODO: subdivision lines (and some funky system to input them)
# 3. "tracks", concentric circles with dots to indicate notes


class CircleRhythmTrackNote(Dot):
    
    def ripple(self) -> RippleOut:
        return RippleOut(
                    focus_point=self,
                    color=self.color,
                    stroke_width=5, max_radius=0.6*(self.radius/DEFAULT_DOT_RADIUS))


class CircleRhythmTrack(VGroup):

    # TODO: implement multiple types of notes

    # mobjects
    mob_circle_background: Circle
    mob_notes: VDict # VDict[int, CircleRhythmTrackNote]

    # properties
    prop_divisions: int
    prop_color: str
    prop_scale_factor: float

    def __init__(self, divisions: int=8, color=WHITE, radius: int=1, scale_factor: float=1, **kwargs):
        VGroup.__init__(self, **kwargs)
        self.prop_divisions = divisions
        self.prop_color = color
        self.prop_scale_factor = scale_factor
        # TODO: replace int notes with fraction notes?
        self.mob_circle_background = Circle(color=color, radius=radius, stroke_opacity=0.3, stroke_width=8*scale_factor).rotate(90 * PI / 180).flip()
        self.mob_notes = VDict(show_keys=False)
        self.add(self.mob_circle_background, self.mob_notes)

    def add_note(self, note_num: int):
        location = self.mob_circle_background.point_from_proportion((note_num-1) / self.prop_divisions)
        note = CircleRhythmTrackNote(point=location, color=self.mob_circle_background.color, radius=DEFAULT_DOT_RADIUS*self.prop_scale_factor)
        return Create(note, _on_finish=callback_add_to_vdict(self.mob_notes, note_num, note))

    # TODO: test and debug with group shenanigans
    def remove_note(self, note_num: int):
        if note_num not in self.mob_notes:
            raise ValueError(f"Tried to remove note {note_num}, but there's no note with that number.")
        note = self.mob_notes[note_num]
        self.mob_notes.remove(note_num)
        return Uncreate(note)

    # TODO: debug
    def play_measure(self) -> Animation:
        animations = []
        for step in range(1, self.prop_divisions+1):
            if step in self.mob_notes:
                animations.append(self.mob_notes[step].ripple())
            else:
                animations.append(Wait())
        print()
        return Succession(*animations)
    

    def add_notes(self, notes: list[int]) -> Animation:
        animations = []
        for step in range(1, self.prop_divisions+1):
            if step in notes:
                animations.append(self.add_note(step))
            else:
                animations.append(Wait())
        return Succession(*animations)


class CircleRhythmPacekeeper(VGroup):
    DEFAULT_BASE_WIDTH = 0.1
    DEFAULT_LENGTH = 1.2

    # mobjects
    mob_pointer: Polygon
    mob_axle: Circle

    def __init__(self, color: str=WHITE, length: float=DEFAULT_LENGTH, width: float=DEFAULT_BASE_WIDTH, **kwargs):
        super().__init__(**kwargs)
        half_width = width / 2
        # pointer
        self.mob_pointer = Polygon(
            [-half_width, 0, 0],
            [half_width, 0, 0],
            [0, length, 0],
        color=color, fill_opacity=1, stroke_width=0)
        self.add(self.mob_pointer)
        # axle
        self.mob_axle = AnnularSector(inner_radius=0, outer_radius=half_width, angle=PI, start_angle=PI, color=color, fill_opacity=1,)
        self.add(self.mob_axle)
    
    # TODO: address bug about self not benig active
    def create(self):
        return AnimationGroup(
            Create(self.mob_pointer),
            Create(self.mob_axle),
        )


class CircleRhythmSubdivisions(VGroup):

    def __init__(self, divisions: list[int]=[4,4], radius: float=1, fade_factor: float=0.7, shrink_factor: float=0.9, color=GRAY_A, **kwargs):
        super().__init__()

        def create_line(radius: float, pct: float, opacity: float=1.0, width: float=DEFAULT_STROKE_WIDTH, start_radius: float=0):
            direction = vector_on_unit_circle_clockwise_from_top(pct)
            x = Line(
                start=direction * start_radius,
                end=direction * radius,
                color=color,
                stroke_opacity=opacity,
                stroke_width=width,
                **kwargs)
            # print(x.stroke_width)
            return x

        # biggest line is always at the top
        self.add(create_line(radius=radius, pct=0))

        # next, go to subdivisions
        total_subdivisions = 1
        for idx, subdivision in enumerate(divisions):
            total_subdivisions *= subdivision
            div_shrink = shrink_factor ** (idx+1)
            div_weight = fade_factor ** (idx+1)
            print(f"entering first loop. {idx=}, {subdivision=}, {total_subdivisions=}, {div_shrink=}, {div_weight=}")

            # draw numbers and circle
            start_radius = 0.1 * radius * (idx + 1.5)
            text_radius = 0.1 * radius * ((idx + 1.5) - 0.5)
            self.add(Circle(
                radius=start_radius,
                color=color,
                stroke_opacity=div_weight,
                stroke_width=(div_weight*DEFAULT_STROKE_WIDTH)))
            self.add(Text(
                text=str(subdivision),
                font_size=8*radius,
                fill_opacity=div_weight)
                .shift(
                    vector_on_unit_circle_clockwise_from_top(0.5) * text_radius,
                    LEFT * radius * 0.03))
            # TODO: will have to be reworked when i handle complex rhythms
            # num_repeats = int(total_subdivisions / subdivision)
            # arc_length = 1 / num_repeats
            # for repeat_num in range(num_repeats):
                # self.add(Text(text=str(subdivision)).shift(vector_on_unit_circle_clockwise_from_top(arc_length * repeat_num + (arc_length/2)) * 0.6 * (idx+1 - 0.5)))

            # draw divisions
            for step in range(total_subdivisions):
                print(f"step {step}, step % subdivision = {step % subdivision}")
                if step % subdivision != 0:
                    print(f"creating line with pct={step / total_subdivisions}")
                    self.add(create_line(
                        start_radius=start_radius,
                        radius=(radius * div_shrink),
                        opacity=div_weight, width=(div_weight*DEFAULT_STROKE_WIDTH),
                        pct=(step / total_subdivisions)))


class SubdivisionsScene(Scene):
    def construct(self):
        self.wait(0.2)
        self.play(Create(CircleRhythmSubdivisions(radius=3, divisions=[4,3])))
        self.wait(1)



class CircleRhythm(VGroup):

    # mobjects
    mob_subdivisions: CircleRhythmSubdivisions
    mob_pacekeeper: CircleRhythmPacekeeper
    mob_tracks: VDict # VDict[id: str, track: CircleRhythmTrack]

    # # properties
    # prop_subdivision # = some data structure to indicate data structure
    # prop_rpm # = revolutions per minute

    # implementation details


    def __init__(self, radius: float=1, divisions: list[int]=[4,4], **kwargs):
        super().__init__(**kwargs)

        # subdivisions
        self.mob_subdivisions = CircleRhythmSubdivisions(radius=radius, divisions=divisions)
        self.add(self.mob_subdivisions)

        # pacekeeper
        self.mob_pacekeeper = CircleRhythmPacekeeper(length=radius, width=radius*0.1)
        self.add(self.mob_pacekeeper)

        # tracks
        self.mob_tracks = VDict()
        self.add(self.mob_tracks)
    
    def add_track(self, id: str, track: CircleRhythmTrack):
        return Create(track, _on_finish=callback_add_to_vdict(self.mob_tracks, id, track))
    
    def play_measure(self) -> Animation:
        return AnimationGroup(
            Rotate(self.mob_pacekeeper, -TAU, about_point=np.array([0, 0, 0]), rate_func=linear, run_time=1),
            *[mob_track.play_measure().set_run_time(1) for mob_track in self.mob_tracks.get_all_submobjects()]
        )
    
    # TODO: fix bug where self isn't created, but all its submobjects are
    def create(self) -> Animation:
        return AnimationGroup(
            DrawBorderThenFill(self),
            # AnimationGroup(
            #     Create(self.mob_notes),
            #     Create(self.mob_select_circles),
            #     Create(self.mob_select_connectors),
            # ),
            lag_ratio=0.2,
            run_time=1,
        )


class test(Scene):
    def construct(self):
        self.wait(0.5 )

        rhythm_circle = CircleRhythm(radius=2, divisions=[4,2])
        self.play(rhythm_circle.create())

        bass_track = CircleRhythmTrack(color=RED, radius=0.4*2, scale_factor=2)
        snare_track = CircleRhythmTrack(color=YELLOW, radius=0.7*2, scale_factor=2)
        hihat_track = CircleRhythmTrack(color=PURPLE, radius=1.0*2, scale_factor=2)
        self.play(
            rhythm_circle.add_track('bass', bass_track),
            rhythm_circle.add_track('snare', snare_track),
            rhythm_circle.add_track('hihat', hihat_track),
            run_time=1
        )
        self.wait(0.5)
        
        self.play(
            bass_track.add_notes([1, 4, 6]),
            snare_track.add_notes([3, 7]),
            hihat_track.add_notes([1, 2, 3, 4, 5, 6, 7, 8]),
            run_time=2
        )
        self.wait(1)

        self.play(rhythm_circle.play_measure(), run_time=3)
        self.wait(1)
