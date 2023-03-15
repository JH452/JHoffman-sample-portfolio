import os
from dotenv import load_dotenv
import hikari
import lightbulb
import requests
import math
import pytesseract
from PIL import Image
import ssl
import json
from io import BytesIO
import bleach


load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DEFAULT_GUILDS = int(os.getenv('DEFAULT_GUILDS'))

# This allows the .json requests to work
ssl._create_default_https_context = ssl._create_unverified_context


# image recognition relies on Google's Tesseract
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def getmortydata(mortynumber):
    # Returns MortyInfo for the given Morty number (Campaign/MortyInfo.json, uses the morty names as Keys)
    output = {}
    for i in C_MortyInfo_full:
        if C_MortyInfo_full[i]['number'] == str(mortynumber):
            output = C_MortyInfo_full[i]
            break
    # output = C_MortyInfo_full[M_MortyInfo_full[mortynumber-1]['morty_id']]   # doesn't work because Multiplayer/MortyInfo.json mortys are not all listed in order
    return output


def list_overlapQ(set1, set2):
    # Returns True if two sorted list ranges overlap else returns false
    overlap = False
    if set1[-1] <= set2[-1]:
        if set1[-1] >= set2[0]:
            overlap = True
    elif set1[0] <= set2[-1]:
        overlap = True
    return overlap


def get_IVs(trainedQ, mortynumber, mortylevel, mortyHP, mortyatk, mortydef, mortyspd, mortyHPbase, mortyatkbase,
            mortydefbase, mortyspdbase):
    # Returns morty IVs as a list
    if mortynumber == 422 and mortylevel == 100 and mortyatk > 343:
        # OG gotron
        mortyatkbase = 110
        mortydefbase = 105

    hpIV = []
    atkIV = []
    defIV = []
    spdIV = []
    for i in range(1, 17):
        if math.floor((int(mortyHPbase) + i + trainedQ * 63 + 50) * mortylevel / 50) + 10 == mortyHP:
            hpIV.append(i)
        if math.floor((int(mortyatkbase) + i + trainedQ * 63) * mortylevel / 50) + 5 == mortyatk:
            atkIV.append(i)
        if math.floor((int(mortydefbase) + i + trainedQ * 63) * mortylevel / 50) + 5 == mortydef:
            defIV.append(i)
        if math.floor((int(mortyspdbase) + i + trainedQ * 63) * mortylevel / 50) + 5 == mortyspd:
            spdIV.append(i)

    return [hpIV, atkIV, defIV, spdIV]


def format_IVs(IVs, err_HP, err_atk, err_def, err_spd):
    # Returns IVs as a string
    if len(IVs[0]) == 1:
        formatted_HP = str(IVs[0][0])
    elif len(IVs[0]) == 0:
        formatted_HP = '-1'
    else:
        formatted_HP = '(' + str(IVs[0][0]) + '-' + str(IVs[0][-1]) + ')'

    if len(IVs[1]) == 1:
        formatted_atk = str(IVs[1][0])
    elif len(IVs[1]) == 0:
        formatted_atk = '-1'
    else:
        formatted_atk = '(' + str(IVs[1][0]) + '-' + str(IVs[1][-1]) + ')'

    if len(IVs[2]) == 1:
        formatted_def = str(IVs[2][0])
    elif len(IVs[2]) == 0:
        formatted_def = '-1'
    else:
        formatted_def = '(' + str(IVs[2][0]) + '-' + str(IVs[2][-1]) + ')'

    if len(IVs[3]) == 1:
        formatted_spd = str(IVs[3][0])
    elif len(IVs[3]) == 0:
        formatted_spd = '-1'
    else:
        formatted_spd = '(' + str(IVs[3][0]) + '-' + str(IVs[3][-1]) + ')'

    if err_HP:
        formatted_HP = ':warning:'
    if err_atk:
        formatted_atk = ':warning:'
    if err_def:
        formatted_def = ':warning:'
    if err_spd:
        formatted_spd = ':warning:'

    return formatted_HP + '/' + formatted_atk + '/' + formatted_def + '/' + formatted_spd


def get_userinput(screenshot, morty_number, morty_hp, morty_atk, morty_def, morty_spd, mortylevel, debug=False):
    if screenshot is not None:
        screenshot = bleach.clean(screenshot)
    if morty_number is not None:
        if str(morty_number).isdigit():
            morty_number = int(morty_number)
    if morty_hp is not None:
        if str(morty_hp).isdigit():
            morty_hp = int(morty_hp)
    if morty_atk is not None:
        if str(morty_atk).isdigit():
            morty_atk = int(morty_atk)
    if morty_def is not None:
        if str(morty_def).isdigit():
            morty_def = int(morty_def)
    if morty_spd is not None:
        if str(morty_spd).isdigit():
            morty_spd = int(morty_spd)
    if mortylevel is not None:
        if str(mortylevel).isdigit():
            mortylevel = int(mortylevel)

    mortynumber_raw = -1
    mortylevel_raw = -1
    mortyHP_raw = -1
    mortyatk_raw = -1
    mortydef_raw = -1
    mortyspd_raw = -1
    mortynumber = -1
    mortyHP = -1
    mortyatk = -1
    mortydef = -1
    mortyspd = -1
    im1 = -1
    im2 = -1
    im3 = -1
    im4 = -1
    im5 = -1
    im6 = -1
    err_HP = False
    err_atk = False
    err_def = False
    err_spd = False
    err_num = False

    ocrerror = ''

    numbererror = ''
    HPerror = ''
    atkerror = ''
    deferror = ''
    spderror = ''

    missingnumber = ''
    missingHP = ''
    missingatk = ''
    missingdef = ''
    missingspd = ''
    missingany = ''

    ocrerrormsg = ":warning: IVbot couldn't read parts of this image - enter it manually instead.\n\n Check that the image is a native screenshot of the in-game stats page (no extended or cropped borders, icons covering numbers, low resolution etc.). If so, try /debug and tell me if the numbers are selected incorrectly. Otherwise, there is a problem with google's pytesseract and there is nothing I can do. <@840261862868516925>\n"

    from_image = False
    if isinstance(screenshot, str):
        stream = requests.get(screenshot, stream=True).raw
        im = Image.open(stream)
        from_image = True

        im_ratio = im.height / im.width
        im_size = [im.width, im.height, im.width, im.height]

        CropChoice = 0

        for i in range(len(CropData)):
            if CropData[i][0] < im_ratio <= CropData[i + 1][0]:
                if abs(im_ratio - CropData[i][0]) <= abs(im_ratio - CropData[i + 1][0]):
                    CropChoice = i
                else:
                    CropChoice = i + 1
                break

    if morty_number is not None and str(morty_number).isdigit():
        try:
            mortynumber = int(morty_number)
            if mortynumber < 1:
                mortynumber = -1
                err_num = True
        except:
            numbererror = ":warning: morty_number currently supports integers between 1 and " + str(len(
                C_MortyInfo_full)) + ". If this is a newer Morty, ask <@121382671371862018> to update the .json data files on the website.\n "
            err_num = True
    elif from_image:
        try:
            im1 = im.crop(tuple([int(round(a * b, 0))
                                 for a, b in zip(im_size, CropData[CropChoice][1])]))
            im1 = im1.convert("L")
            im1 = im1.point(lambda p: p < 60 and 255)
            mortynumber_raw = pytesseract.image_to_string(im1, lang='eng')
            mortynumber = int(mortynumber_raw.split("#", 1)[1][:3])
        except:
            ocrerror = ocrerrormsg
            err_num = True
    else:
        missingnumber = ":warning: You need to provide the morty_number (or a screenshot)!\n"
        err_num = True

    if mortynumber > len(C_MortyInfo_full):
        mortynumber = -1
        numbererror = ":warning: morty_number currently supports integers between 1 and " + str(len(
            C_MortyInfo_full)) + ". If this is a newer Morty, ask <@121382671371862018> to update the .json data files on the website.\n "
        err_num = True

    if morty_hp is not None and str(morty_hp).isdigit():
        try:
            mortyHP = int(morty_hp)
            if mortyHP < 1:
                HPerror = ":warning: The morty_hp: '" + \
                          str(morty_hp) + "' is not valid.\n"
                err_HP = True

        except:
            HPerror = ":warning: The morty_hp: '" + morty_hp + "' is not valid.\n"
            err_HP = True
    elif from_image:
        try:
            im3 = im.crop(tuple([int(round(a * b, 0))
                                 for a, b in zip(im_size, CropData[CropChoice][3])]))
            im3 = im3.convert("L")
            mortyHP_raw = pytesseract.image_to_string(im3, lang='eng')
            mortyHP = int(''.join(filter(str.isdigit, mortyHP_raw)))
        except:
            ocrerror = ocrerrormsg
            err_HP = True
    else:
        missingHP = ":warning: You need to provide the morty_hp (or a screenshot)!\n"
        err_HP = True

    if morty_atk is not None and str(morty_atk).isdigit():
        try:
            mortyatk = int(morty_atk)
            if mortyatk < 1:
                atkerror = ":warning: The morty_hp: '" + \
                           str(mortyatk) + "' is not valid.\n"
                err_atk = True
        except:
            atkerror = ":warning: The morty_atk: '" + morty_atk + "' is not valid.\n"
            err_atk = True
    elif from_image:
        try:
            im4 = im.crop(tuple([int(round(a * b, 0))
                                 for a, b in zip(im_size, CropData[CropChoice][4])]))
            im4 = im4.convert("L")
            mortyatk_raw = pytesseract.image_to_string(im4, lang='eng')
            mortyatk = int(''.join(filter(str.isdigit, mortyatk_raw)))
        except:
            ocrerror = ocrerrormsg
            err_atk = True
    else:
        missingatk = ":warning: You need to provide the morty_atk (or a screenshot)!\n"
        err_atk = True

    if morty_def is not None and str(morty_def).isdigit():
        try:
            mortydef = int(morty_def)
            if mortydef < 1:
                deferror = ":warning: The morty_hp: '" + \
                           str(mortydef) + "' is not valid.\n"
                err_def = True
        except:
            deferror = ":warning: The morty_def: '" + morty_def + "' is not valid.\n"
            err_def = True
    elif from_image:
        try:
            im5 = im.crop(tuple([int(round(a * b, 0))
                                 for a, b in zip(im_size, CropData[CropChoice][5])]))
            im5 = im5.convert("L")
            mortydef_raw = pytesseract.image_to_string(im5, lang='eng')
            mortydef = int(''.join(filter(str.isdigit, mortydef_raw)))
        except:
            ocrerror = ocrerrormsg
            err_def = True
    else:
        missingdef = ":warning: You need to provide the morty_def (or a screenshot)!\n"
        err_def = True

    if morty_spd is not None and str(morty_spd).isdigit():
        try:
            mortyspd = int(morty_spd)
            if mortyspd < 1:
                spderror = ":warning: The morty_hp: '" + \
                           str(mortyspd) + "' is not valid.\n"
                err_spd = True
        except:
            spderror = ":warning: The morty_spd: '" + morty_spd + "' is not valid.\n"
            err_spd = True
    elif from_image:
        try:
            im6 = im.crop(tuple([int(round(a * b, 0))
                                 for a, b in zip(im_size, CropData[CropChoice][6])]))
            im6 = im6.convert("L")
            mortyspd_raw = pytesseract.image_to_string(im6, lang='eng')
            mortyspd = int(''.join(filter(str.isdigit, mortyspd_raw)))
        except:
            ocrerror = ocrerrormsg
            err_spd = True
    else:
        missingspd = ":warning: You need to provide the morty_spd (or a screenshot)!\n"
        err_spd = True

    if all(item is None for item in [morty_number, morty_hp, morty_atk, morty_def, morty_spd, screenshot]):
        missingnumber = ''
        missingHP = ''
        missingatk = ''
        missingdef = ''
        missingspd = ''
        missingany = ":warning: You need to provide a screenshot or the morty_number and at least one stat!\n"

    er_message = numbererror + HPerror + atkerror + deferror + spderror \
                 + missingnumber + missingHP + missingatk + missingdef + missingspd \
                 + ocrerror + missingany

    if debug:
        if from_image:
            try:
                im2 = im.crop(
                    tuple([int(round(a * b, 0)) for a, b in zip(im_size, CropData[CropChoice][2])]))
                im2 = im2.convert("L")
                im2 = im2.point(lambda p: p < 60 and 255)
                mortylevel_raw = pytesseract.image_to_string(im2, lang='eng')
                mortylevel = int(''.join(filter(str.isdigit, mortylevel_raw)))
            except:
                mortylevel = -1

    if debug:
        return [mortynumber_raw, mortylevel_raw, mortyHP_raw, mortyatk_raw, mortydef_raw, mortyspd_raw, mortynumber,
                mortylevel, mortyHP, mortyatk, mortydef, mortyspd, im1, im2, im3, im4, im5, im6]
    else:
        return [er_message, mortynumber, mortyHP, mortyatk, mortydef, mortyspd, err_HP, err_atk, err_def, err_spd,
                err_num]


def get_concat_h_blank(im1, im2, im3, im4, im5, im6, color=(0, 0, 0)):
    dst = Image.new('RGB', (im1.width + im2.width + im3.width + im4.width + im5.width + im6.width,
                            max(im1.height, im2.height, im3.height, im4.height, im5.height, im6.height)), color)
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    dst.paste(im3, (im1.width + im2.width, 0))
    dst.paste(im4, (im1.width + im2.width + im3.width, 0))
    dst.paste(im5, (im1.width + im2.width + im3.width + im4.width, 0))
    dst.paste(im6, (im1.width + im2.width +
                    im3.width + im4.width + im5.width, 0))
    return dst


def validstats(mortynumber, mortylevel, mortyHP, mortyatk, mortydef, mortyspd, mortyHPbase, mortyatkbase, mortydefbase,
               mortyspdbase):
    if mortynumber == 422 and mortylevel == 100 and mortyatk > 343:
        # OG gotron
        mortyatkbase = 110
        mortydefbase = 105
    output = []
    minHP = math.floor((int(mortyHPbase) + 1 + 50) * mortylevel / 50) + 10
    maxHP = math.floor((int(mortyHPbase) + 16 + 63 + 50)
                       * mortylevel / 50) + 10
    if minHP <= int(mortyHP) <= maxHP or -1 in [int(mortyHP), int(mortyHPbase)]:
        output.append(True)
    else:
        output.append(False)

    for i in [[mortyatk, mortyatkbase], [mortydef, mortydefbase], [mortyspd, mortyspdbase]]:
        minstat = math.floor((int(i[1]) + 1) * mortylevel / 50) + 5
        maxstat = math.floor((int(i[1]) + 16 + 63) * mortylevel / 50) + 5
        if minstat <= int(i[0]) <= maxstat or -1 in [int(i[0]), int(i[1])]:
            output.append(True)
        else:
            output.append(False)

    return output


# Emoji symbols
buff = '<:buff:705887874641297439>'
debuff = '<:debuff:705887932862562304>'
paralyze = '<:paralyze:642150490351599617>'
poison = '<:poison:642149702317637632>'
rock = '<:rock:338843657077653514>'
paper = '<:paper:338843687691747329>'
scissors = '<:scissors:338843616774455296>'
absorb = '<:absorb:731618575898640465>'
stop = ':stop_button:'
fastf = ':fast_forward:'
rarity = ['<:common:642173768357380137>', '<:rare:642173787449851915>',
          '<:epic:642173805690748954>', '<:exotic:642173814737862688>']
mseed = '<:MegaSeed:337366785118699520>'

# crop data for different screenshot aspect ratios - a higher ratio is more square
CropData = [
    [
        0.3897,
        [0.066606661, 0.064665127, 0.126012601, 0.120092379],
        [0.387038704, 0.406466513, 0.432043204, 0.473441109],
        [0.773177318, 0.219399538, 0.810081008, 0.27482679],
        [0.773177318, 0.300230947, 0.810081008, 0.357967667],
        [0.773177318, 0.383371824, 0.810081008, 0.438799076],
        [0.773177318, 0.459584296, 0.810081008, 0.515011547]
    ],
    [
        0.4365,
        [0.078008299, 0.041825095, 0.141908714, 0.096958175],
        [0.371784232, 0.401140684, 0.42406639, 0.456273764],
        [0.814107884, 0.207224335, 0.859751037, 0.260456274],
        [0.814107884, 0.285171103, 0.859751037, 0.344106464],
        [0.814107884, 0.368821293, 0.859751037, 0.425855513],
        [0.814107884, 0.452471483, 0.859751037, 0.507604563]
    ],
    [
        0.4497,
        [0.074812968, 0.059149723, 0.139650873, 0.121996303],
        [0.373233583, 0.397351201, 0.425965087, 0.469500924],
        [0.814630091, 0.220356747, 0.859517872, 0.275264325],
        [0.814630091, 0.303142329, 0.859517872, 0.354898336],
        [0.814630091, 0.382624769, 0.859517872, 0.436229205],
        [0.814630091, 0.463955638, 0.859517872, 0.515711645]
    ],
    [
        0.4618,
        [0.078683036, 0.061594203, 0.142299107, 0.120772947],
        [0.368303571, 0.404589372, 0.421875, 0.471014493],
        [0.820870536, 0.225845411, 0.869977679, 0.274154589],
        [0.820870536, 0.305555556, 0.869977679, 0.358695652],
        [0.820870536, 0.380434783, 0.869977679, 0.435990338],
        [0.820870536, 0.464975845, 0.869977679, 0.518115942]
    ],
    [
        0.4737,
        [0.075236842, 0.0605, 0.151315789, 0.117277778],
        [0.365131579, 0.408333333, 0.418421053, 0.466666667],
        [0.830921053, 0.223611111, 0.876315789, 0.275],
        [0.830921053, 0.3, 0.876315789, 0.354166667],
        [0.830921053, 0.381944444, 0.876315789, 0.436111111],
        [0.830921053, 0.461111111, 0.876315789, 0.5125]
    ],
    [
        0.4798,
        [0.075236842, 0.0605, 0.151315789, 0.117277778],
        [0.381809095, 0.404166667, 0.433783108, 0.470833333],
        [0.855572214, 0.216666667, 0.903548226, 0.275],
        [0.855572214, 0.3, 0.903548226, 0.354166667],
        [0.855572214, 0.38125, 0.903548226, 0.435416667],
        [0.855572214, 0.458333333, 0.903548226, 0.516666667],
    ],
    [
        0.4863,  # MINE
        [0.081938326, 0.059782609, 0.153303965, 0.119565217],
        [0.362114537, 0.407608696, 0.416740088, 0.467391304],
        [0.839647577, 0.217391304, 0.888105727, 0.277173913],
        [0.839647577, 0.304347826, 0.888105727, 0.356884058],
        [0.839647577, 0.384057971, 0.888105727, 0.434782609],
        [0.839647577, 0.46557971, 0.888105727, 0.514492754]
    ],
    [
        0.500,
        [0.081938326, 0.059782609, 0.153303965, 0.119565217],
        [0.355114537, 0.407608696, 0.416740088, 0.467391304],
        [0.849647577, 0.217391304, 0.898105727, 0.277173913],
        [0.849647577, 0.304347826, 0.898105727, 0.356884058],
        [0.849647577, 0.384057971, 0.898105727, 0.434782609],
        [0.849647577, 0.46557971, 0.898105727, 0.514492754]
    ],
    [
        0.5630,
        (0.0950537815, 0.060298507, 0.18907563, 0.130597015),
        (0.340882353, 0.401119403, 0.419159664, 0.465089552),
        (0.885344538, 0.218283582, 0.953621849, 0.270522388),
        (0.885344538, 0.298507463, 0.953621849, 0.348880597),
        (0.885344538, 0.373134328, 0.953621849, 0.429104478),
        (0.885344538, 0.457761194, 0.953621849, 0.513731343)
    ],
    [
        0.749,  # ipad
        [0.096, 0.048042705, 0.174666667, 0.088967972],
        [0.337333333, 0.432384342, 0.421598, 0.475088968],
        [0.893333333, 0.286476868, 0.949333333, 0.332740214],
        [0.893333333, 0.350533808, 0.949333333, 0.391459075],
        [0.893333333, 0.411032028, 0.949333333, 0.451957295],
        [0.893333333, 0.471530249, 0.949333333, 0.510676157]
    ],
    [10]
]

C_MortyInfo_file = open("src/data/Campaign/MortyInfo.json")
C_MortyInfo_full = json.load(C_MortyInfo_file)

M_MortyInfo_file = open("src/data/Multiplayer/MortyInfo.json")
M_MortyInfo_full = json.load(M_MortyInfo_file)

mortyEN_file = open("src/data/EN.json")
mortyEN_full = json.load(mortyEN_file)

AttackInfo_file = open("src/data/Multiplayer/AttackInfo.json")
AttackInfo_full = json.load(AttackInfo_file)

bot = lightbulb.BotApp(
    token=DISCORD_TOKEN,
    default_enabled_guilds=(DEFAULT_GUILDS)
)


@bot.command
@lightbulb.command('help', 'help screen')
@lightbulb.implements(lightbulb.SlashCommand)
async def help(ctx: lightbulb.Context) -> None:
    message = "How to use **/ivs**\n> • Type '/ivs' and select the command.\n> • Enter the Morty level into the field 'morty_level'.\n> • Add the field 'screenshot' and upload an in-game screenshot of the Morty stats page.\n> • Press enter to run the command.\n> \n> Alternatively, you can enter any of the morty stats manually by adding the relevant field(s). Manually entered stats override the stats pulled from an image.\n\n"
    message += "How to use **/predictivs**\n> Same input as with the /ivs command, except it includes the 'seed_assumption' parameter in the form [x,y,z], where x, y, and z are the number of attack, defense, and speed mega seeds that have been used, respectively. Leave 'seed_assumption' blank and it will run with the default value of [0,0,0].\n\n"
    message += "**F.A.Q.**\n\n"
    message += "Is /predictivs accurate?\n> If the seed assumptions that you provide are correct, the true IVs will be within the stated ranges. However, if a Morty was partly trained while as a previous evolution, or if it is/was a pre-nerf Gotron, /predictivs will not work.\n\n"
    message += "'Morty Bot' was written by <@840261862868516925> - ask me if there is something that I haven't covered here."

    embed = hikari.Embed(
        title='/help', color=(150, 150, 150), description=message)

    await ctx.respond(embed)


@bot.command
@lightbulb.option("morty_number", "morty number", type=hikari.OptionType.INTEGER, required=True)
@lightbulb.command('lookup', 'get info on a morty')
@lightbulb.implements(lightbulb.SlashCommand)
async def lookup(ctx: lightbulb.Context) -> None:
    message = ''
    numbererror = ''
    mortyname = 'morty_name'
    err_num = False
    errormsg = "\n\n:warning: morty_number currently supports integers between 1 and " + str(len(
        C_MortyInfo_full)) + ". If this is a newer Morty, ask <@121382671371862018> to update the .json data files on the website.\n "

    if str(ctx.options.morty_number).isdigit():
        mortynumber = ctx.options.morty_number
    else:
        message = errormsg
        err_num = True

    try:
        mortynumber = int(mortynumber)
        if mortynumber < 1 or mortynumber > len(C_MortyInfo_full):
            message = errormsg
            err_num = True
    except:
        message = errormsg
        err_num = True

    if err_num:
        embed = hikari.Embed(title=mortyname + ':', color=(150, 150, 150),
                             description=message)
        embed.set_thumbnail(
            'https://media.discordapp.net/attachments/1013921169415614507/1018045899789848576/000.png')
    else:
        mortydata = getmortydata(mortynumber)

        mortyname = mortyEN_full['Morty'][mortydata['id']]['name']
        mortyHPbase = mortydata['hpbase']
        mortyatkbase = mortydata['attackbase']
        mortydefbase = mortydata['defencebase']
        mortyspdbase = mortydata['speedbase']

        HPlevels16 = []
        HPlevels15 = []
        Atklevels16 = []
        Deflevels16 = []
        Spdlevels16 = []

        for i in range(5, 51):
            HP16 = math.floor((int(mortyHPbase) + 16 + 50) * i / 50)
            HP15 = math.floor((int(mortyHPbase) + 15 + 50) * i / 50)
            HP14 = math.floor((int(mortyHPbase) + 15) * i / 50)
            Atk16 = math.floor((int(mortyatkbase) + 16) * i / 50)
            Atk15 = math.floor((int(mortyatkbase) + 15) * i / 50)
            Def16 = math.floor((int(mortydefbase) + 16) * i / 50)
            Def15 = math.floor((int(mortydefbase) + 15) * i / 50)
            Spd16 = math.floor((int(mortyspdbase) + 16) * i / 50)
            Spd15 = math.floor((int(mortyspdbase) + 15) * i / 50)
            if HP15 < HP16:
                HPlevels16.append(i)
            if HP14 < HP15:
                HPlevels15.append(i)
            if Atk15 < Atk16:
                Atklevels16.append(i)
            if Def15 < Def16:
                Deflevels16.append(i)
            if Spd15 < Spd16:
                Spdlevels16.append(i)

        if len(HPlevels16) == 46:
            HPlevels16 = '[5, ...]'
        else:
            for i in range(len(HPlevels16) - 1, 0, -1):
                if HPlevels16[i] - HPlevels16[i - 1] != 1:
                    HPlevels16 = str(HPlevels16[:i + 1])[:-1] + ', ...]'
                    break
        if len(HPlevels15) == 46:
            HPlevels15 = '[5, ...]'
        else:
            for i in range(len(HPlevels15) - 1, 0, -1):
                if HPlevels15[i] - HPlevels15[i - 1] != 1:
                    HPlevels15 = str(HPlevels15[:i + 1])[:-1] + ', ...]'
                    break
        if len(Atklevels16) == 46:
            Atklevels16 = '[5, ...]'
        else:
            for i in range(len(Atklevels16) - 1, 0, -1):
                if Atklevels16[i] - Atklevels16[i - 1] != 1:
                    Atklevels16 = str(Atklevels16[:i + 1])[:-1] + ', ...]'
                    break
        if len(Deflevels16) == 46:
            Deflevels16 = '[5, ...]'
        else:
            for i in range(len(Deflevels16) - 1, 0, -1):
                if Deflevels16[i] - Deflevels16[i - 1] != 1:
                    Deflevels16 = str(Deflevels16[:i + 1])[:-1] + ', ...]'
                    break
        if len(Spdlevels16) == 46:
            Spdlevels16 = '[5, ...]'
        else:
            for i in range(len(Spdlevels16) - 1, 0, -1):
                if Spdlevels16[i] - Spdlevels16[i - 1] != 1:
                    Spdlevels16 = str(Spdlevels16[:i + 1])[:-1] + ', ...]'
                    break

        HPlevels16str = ''.join(str(HPlevels16))
        HPlevels15str = ''.join(str(HPlevels15))
        Atklevels16str = ''.join(str(Atklevels16))
        Deflevels16str = ''.join(str(Deflevels16))
        Spdlevels16str = ''.join(str(Spdlevels16))
        IVlevels = '**Levels to determine IVs (0 EVs):**\n> **(16 HP):** ' + HPlevels16str + '\n> **(15+ HP):** ' + HPlevels15str + \
                   '\n> **(16 Atk):** ' + Atklevels16str + '\n> **(16 Def):** ' + \
                   Deflevels16str + '\n> **(16 Spd):** ' + Spdlevels16str

        message = 'Base stats: ' + mortyHPbase + ' HP, ' + mortyatkbase + ' Atk, ' + \
                  mortydefbase + ' Def, ' + mortyspdbase + \
                  ' Spd\n\n' + IVlevels + "\n\n**Attacks:**\n"

        attacks = mortydata['attacks'].split(",")

        mortytype = ""
        if mortydata['elementtype'] == "Rock":
            mortytype = rock
        elif mortydata['elementtype'] == "Paper":
            mortytype = paper
        elif mortydata['elementtype'] == "Scissors":
            mortytype = scissors

        mortyrarity = rarity[int(mortydata['division']) - 1]

        for attack in [' ' + attacks[0]] + attacks[1:]:
            attackid = attack.split(":")[0][1:]
            attacklvl = attack.split(":")[1]

            attackname = ''
            for i in attackid[6:]:
                if i.isupper():
                    attackname += ' '
                attackname += i

            attackAP = ''
            attackdesc = ''

            for AttackInfo in AttackInfo_full:
                if AttackInfo['attack_id'] == attackid:
                    attackAP = AttackInfo['pp_stat']
                    if AttackInfo['element'] == 'Rock':
                        attacktype = rock + ' ' + AttackInfo['element']
                    elif AttackInfo['element'] == 'Paper':
                        attacktype = paper + ' ' + AttackInfo['element']
                    elif AttackInfo['element'] == 'Scissors':
                        attacktype = scissors + ' ' + AttackInfo['element']
                    else:
                        attacktype = 'Normal'

                    for effect in AttackInfo['effects']:
                        try:
                            if effect['accuracy'] > 0:
                                effectAccuracy = str(
                                    effect['accuracy'] * 100) + '%'
                        except:
                            effectAccuracy = '100%'

                        if effect != AttackInfo['effects'][-1]:
                            try:
                                if effect['continue_on_miss'] == False:
                                    effectAccuracy += ' ' + stop
                            except:
                                effectAccuracy += ' ' + fastf

                        if effect['type'] == "Hit":
                            effecttype = attacktype
                            effectPower = 'Power: ' + str(effect['power'])
                        elif effect['type'] == "Absorb":
                            effecttype = absorb + ' Absorb'
                            effectPower = 'Power: ' + str(effect['power'])
                        elif effect['type'] == "Stat":
                            if effect['power'] > 0:
                                effecttype = buff + ' '
                            else:
                                effecttype = debuff + ' '
                            effecttype += effect['stat']
                            if abs(effect['power']) == 1:
                                effectPower = 'Weak'
                            elif abs(effect['power']) == 2:
                                effectPower = 'Medium'
                            elif abs(effect['power']) == 3:
                                effectPower = 'Strong'
                            else:
                                effectPower = 'Very Weak'
                        elif effect['type'] == "Paralyse":
                            effecttype = paralyze + ' Paralyze'

                        else:
                            effecttype = poison + ' Poison'
                        try:
                            if effect['to_self']:
                                effecttype += ' (Self)'
                        except:
                            effecttype += ' (Enemy)'
                        attackdesc += '\n' + "> " + effecttype + ', ' + \
                                      effectPower + ', ' + effectAccuracy  # str(effect)
                    break

            message += 'L.' + attacklvl + ': **' + attackname + \
                       '** (' + str(attackAP) + ' AP)' + attackdesc + '\n'

        embed = hikari.Embed(title='#' + str(mortynumber) + ' ' + mortyname + ' ' + mortyrarity + ' ' + mortytype,
                             color=(150, 150, 150),
                             description=message + numbererror)
        embed.set_thumbnail(
            'https://pocketmortys.net/images/assets/' + mortydata['assetid'] + 'Down_1.png')

    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)


@bot.command
@lightbulb.option("screenshot", "stats page screenshot", type=hikari.OptionType.ATTACHMENT, required=True)
@lightbulb.command('debug', 'debug')
@lightbulb.implements(lightbulb.SlashCommand)
async def debug(ctx: lightbulb.Context) -> None:
    if ctx.options.screenshot is not None:
        screenshot_input = ctx.options.screenshot
        media_type = screenshot_input.media_type
        if media_type is not None and 'image' in media_type:
            screenshot = bleach.clean(screenshot_input.url)
        else:
            screenshot = None
    else:
        screenshot = None

    ocroutput = get_userinput(screenshot, None, None,
                              None, None, None, -1, debug=True)

    ocroutput_concat = get_concat_h_blank(
        ocroutput[12], ocroutput[13], ocroutput[14], ocroutput[15], ocroutput[16], ocroutput[17], color=(0, 0, 0))

    with BytesIO() as image_binary:
        ocroutput_concat.save(image_binary, 'PNG')
        image_binary.seek(0)

        await ctx.respond(hikari.Bytes(image_binary, 'image.png'), flags=hikari.MessageFlag.EPHEMERAL)

    await ctx.respond(str(ocroutput[:6]) + '\n' + str(ocroutput[6:12]), flags=hikari.MessageFlag.EPHEMERAL)


@bot.command
@lightbulb.option("morty_spd", "morty speed stat", type=hikari.OptionType.INTEGER, required=False)
@lightbulb.option("morty_def", "morty defense stat", type=hikari.OptionType.INTEGER, required=False)
@lightbulb.option("morty_atk", "morty attack stat", type=hikari.OptionType.INTEGER, required=False)
@lightbulb.option("morty_hp", "morty hp stat", type=hikari.OptionType.INTEGER, required=False)
@lightbulb.option("morty_level", "morty level", type=hikari.OptionType.INTEGER, required=True)
@lightbulb.option("morty_number", "morty number", type=hikari.OptionType.INTEGER, required=False)
@lightbulb.option("screenshot", "stats page screenshot", type=hikari.OptionType.ATTACHMENT, required=False)
@lightbulb.option("seed_assumption", "seeds used ([0,0,0] by default)", required=False)
@lightbulb.command('predictivs', 'Predicts Morty IVs from a stats page screenshot and/or given stats')
@lightbulb.implements(lightbulb.SlashCommand)
async def predictIVs(ctx: lightbulb.Context) -> None:
    if ctx.options.screenshot is not None:
        screenshot_input = ctx.options.screenshot
        media_type = screenshot_input.media_type
        if media_type is not None and 'image' in media_type:
            screenshot = bleach.clean(screenshot_input.url)
        else:
            screenshot = None
    else:
        screenshot = None

    message = ''
    er_message = ''
    err_level = False

    try:
        seeds = bleach.clean(ctx.options.seed_assumption)[1:-1]
        seeds = [int(i) for i in seeds.split(",")]
    except:
        seeds = [0, 0, 0]  # use default [0,0,0] seeds

    try:
        mortylevel = ctx.options.morty_level
        if mortylevel < 5 or mortylevel > 100:
            mortylevel = -1
            er_message = er_message + ':warning: morty_level must be an integer between 5 and 100.\n'
            err_level = True
    except:
        mortylevel = -1
        er_message = er_message + ':warning: morty_level must be an integer between 5 and 100.\n'
        err_level = True

    userinput = get_userinput(screenshot, ctx.options.morty_number,
                              ctx.options.morty_hp, ctx.options.morty_atk,
                              ctx.options.morty_def, ctx.options.morty_spd, mortylevel)

    er_message = er_message + userinput[0]
    mortynumber = userinput[1]
    mortyHP = userinput[2]
    mortyatk = userinput[3]
    mortydef = userinput[4]
    mortyspd = userinput[5]
    err_HP = userinput[6]
    err_atk = userinput[7]
    err_def = userinput[8]
    err_spd = userinput[9]
    err_num = userinput[10]

    if mortynumber == -1:
        mortydata = getmortydata(1)
    else:
        mortydata = getmortydata(mortynumber)
    mortyname = mortyEN_full['Morty'][mortydata['id']]['name']
    mortyHPbase = mortydata['hpbase']
    mortyatkbase = mortydata['attackbase']
    mortydefbase = mortydata['defencebase']
    mortyspdbase = mortydata['speedbase']

    mortytype = ""
    if mortydata['elementtype'] == "Rock":
        mortytype = rock
    elif mortydata['elementtype'] == "Paper":
        mortytype = paper
    elif mortydata['elementtype'] == "Scissors":
        mortytype = scissors

    mortyrarity = rarity[int(mortydata['division']) - 1]

    validstatslist = validstats(mortynumber, mortylevel, mortyHP, mortyatk, mortydef, mortyspd, mortyHPbase,
                                mortyatkbase, mortydefbase, mortyspdbase)

    if False in validstatslist:
        if not validstatslist[0]:
            er_message += ':warning: The HP stat: ' + \
                          str(mortyHP) + ' is incorrect.\n'
        if not validstatslist[1]:
            er_message += ':warning: The Atk stat: ' + \
                          str(mortyatk) + ' is incorrect.\n'
        if not validstatslist[2]:
            er_message += ':warning: The Def stat: ' + \
                          str(mortydef) + ' is incorrect.\n'
        if not validstatslist[3]:
            er_message += ':warning: The Spd stat: ' + \
                          str(mortyspd) + ' is incorrect.\n'
    elif -1 not in [mortyHP, mortyatk, mortydef, mortyspd]:
        HPIVs = []
        HPiv_dazes = []

        XPlimit = 0
        XPtrack = 0
        maximumdazes = 0
        maxHPEVdazes = math.ceil(65535 / int(mortyHPbase))
        for i in range(5, mortylevel):  # from 5 to (current level)-1
            XPlimit += math.floor((3 * i ** 2 + 3 * i + 1))
            if i - 5 == 0:
                lvlmodifier = 1
            elif i - 5 == 1:
                lvlmodifier = 0.75
            elif i - 5 == 2:
                lvlmodifier = 0.5
            elif i - 5 == 3:
                lvlmodifier = 0.25
            else:
                lvlmodifier = 0.2
            DXP = math.floor(
                ((50 * 5) / (14 / 3)) * lvlmodifier * 0.3)  # xp gain x0.3 by bringing out 4 additional mortys
            while XPtrack < XPlimit and maximumdazes < maxHPEVdazes:
                XPtrack += DXP
                maximumdazes += 1
            if maximumdazes == maxHPEVdazes:
                break
        for HPiv in range(1, 17):
            dazes = []
            for d in range(1 + maximumdazes):
                HPstat = math.floor((int(mortyHPbase) + HPiv + math.floor(
                    math.sqrt(min(d * int(mortyHPbase), 65535)) / 4) + 50) * mortylevel / 50) + 10
                if HPstat == mortyHP:
                    dazes.append(d)
                elif HPstat > mortyHP:
                    break
            HPiv_dazes.append(dazes)
            if dazes != []:
                HPIVs.append(HPiv)
        PossibleHPIVs = []
        PossibleAtkIVs = []
        PossibleDefIVs = []
        PossibleSpdIVs = []
        for atkiv in range(1, 17):
            for defiv in range(1, 17):
                for spdiv in range(1, 17):
                    HPIV = math.floor((atkiv + defiv + spdiv) / 3)
                    if HPIV in HPIVs:
                        for d in HPiv_dazes[HPIV - 1]:
                            if mortyatk == math.floor((int(mortyatkbase) + atkiv + math.floor(math.sqrt(
                                    min(d * int(mortyatkbase) + 2560 * seeds[0], 65535)) / 4)) * mortylevel / 50) + 5:
                                if mortydef == math.floor((int(mortydefbase) + defiv + math.floor(math.sqrt(
                                        min(d * int(mortydefbase) + 2560 * seeds[1],
                                            65535)) / 4)) * mortylevel / 50) + 5:
                                    if mortyspd == math.floor((int(mortyspdbase) + spdiv + math.floor(math.sqrt(
                                            min(d * int(mortyspdbase) + 2560 * seeds[2],
                                                65535)) / 4)) * mortylevel / 50) + 5:
                                        if HPIV not in PossibleHPIVs:
                                            PossibleHPIVs.append(HPIV)
                                        if atkiv not in PossibleAtkIVs:
                                            PossibleAtkIVs.append(atkiv)
                                        if defiv not in PossibleDefIVs:
                                            PossibleDefIVs.append(defiv)
                                        if spdiv not in PossibleSpdIVs:
                                            PossibleSpdIVs.append(spdiv)

        PossibleHPIVs.sort()
        PossibleAtkIVs.sort()
        PossibleDefIVs.sort()
        PossibleSpdIVs.sort()

        if PossibleHPIVs != []:
            message += 'Assuming ' + str(seeds) + ' seeds:' + "\n\n" + 'Possible IVs: ' + format_IVs(
                [PossibleHPIVs, PossibleAtkIVs, PossibleDefIVs, PossibleSpdIVs], err_HP, err_atk, err_def, err_spd)

        elif HPIVs != []:
            message += ':warning: The assumption of ' + str(
                seeds) + ' seeds is __**probably incorrect**__ (!) unless the HP EV is maxed out.' + '\n\nAssuming (unlikely) ' + str(
                seeds) + ' seeds and max HP EV:\n'

            dmin = maxHPEVdazes

            HPIVs = []
            for HPIV in range(1, 17):
                HPstat = math.floor((int(mortyHPbase) + HPIV + 63 + 50) * mortylevel / 50) + 10
                if HPstat == mortyHP:
                    HPIVs.append(HPIV)

            PossibleHPIVs = []
            PossibleAtkIVs = []
            PossibleDefIVs = []
            PossibleSpdIVs = []

            for atkiv in range(1, 17):
                if mortyatk > math.floor((int(mortyatkbase) + atkiv + 63) * mortylevel / 50) + 5:
                    continue
                if mortyatk < math.floor((int(mortyatkbase) + atkiv + math.floor(
                        math.sqrt(min(dmin * int(mortyatkbase), 65535)) / 4)) * mortylevel / 50) + 5:
                    continue
                for defiv in range(1, 17):
                    if mortydef > math.floor((int(mortydefbase) + defiv + 63) * mortylevel / 50) + 5:
                        continue
                    if mortydef < math.floor((int(mortydefbase) + defiv + math.floor(
                            math.sqrt(min(dmin * int(mortydefbase), 65535)) / 4)) * mortylevel / 50) + 5:
                        continue
                    for spdiv in range(1, 17):
                        if mortyspd > math.floor((int(mortyspdbase) + defiv + 63) * mortylevel / 50) + 5:
                            continue
                        if mortyspd < math.floor((int(mortyspdbase) + defiv + math.floor(
                                math.sqrt(min(dmin * int(mortyspdbase), 65535)) / 4)) * mortylevel / 50) + 5:
                            continue
                        HPIV = math.floor((atkiv + defiv + spdiv) / 3)
                        if HPIV in HPIVs:
                            if HPIV not in PossibleHPIVs:
                                PossibleHPIVs.append(atkiv)
                            if atkiv not in PossibleAtkIVs:
                                PossibleAtkIVs.append(atkiv)
                            if defiv not in PossibleDefIVs:
                                PossibleDefIVs.append(defiv)
                            if spdiv not in PossibleSpdIVs:
                                PossibleSpdIVs.append(spdiv)

            PossibleHPIVs.sort()
            PossibleAtkIVs.sort()
            PossibleDefIVs.sort()
            PossibleSpdIVs.sort()

            PossibleIVs = [PossibleHPIVs, PossibleAtkIVs, PossibleDefIVs, PossibleSpdIVs]

            if PossibleIVs != [[], [], [], []]:
                message += 'Possible IVs: ' + \
                           format_IVs(PossibleIVs, err_HP, err_atk,
                                      err_def, err_spd) + '\n\n'
            else:
                message = ':warning: Check for errors in the assumptions of ' + str(
                    seeds) + ' seeds or the stats entered. '
                if mortydata['evolutiontier'] != '1':
                    message += "If not, this Morty was partly trained as a previous evolution; /predictivs currently doesn't work in this case."
                if mortynumber == 422:
                    message += "If not, this Morty was partly trained as a pre-nerf Gotron; /predictivs currently doesn't work in this case."
        else:
            message = ':warning: Check for errors in the assumptions of ' + str(
                seeds) + ' seeds or the stats entered. '
            if mortydata['evolutiontier'] != '1':
                message += "If not, this Morty was partly trained as a previous evolution; /predictivs currently doesn't work in this case."
            if mortynumber == 422:
                message += "If not, this Morty was partly trained as a pre-nerf Gotron; /predictivs currently doesn't work in this case."

    if er_message != '':
        message = er_message

    if mortynumber == -1:
        mortyname = "morty_name"
    else:
        mortyname = mortyname

    if mortynumber == 422 and mortylevel == 100 and (mortyatk > 343 or mortydef > 353):
        mortyname = '(OG) ' + mortyname
        message = ':warning: This is an OG Gotron ... use /ivs for this.'

    if err_level:
        mortylevel = ':warning:'
    else:
        mortylevel = str(mortylevel)
    if err_HP:
        mortyHP = ':warning:'
    else:
        mortyHP = str(mortyHP)
    if err_atk:
        mortyatk = ':warning:'
    else:
        mortyatk = str(mortyatk)
    if err_def:
        mortydef = ':warning:'
    else:
        mortydef = str(mortydef)
    if err_spd:
        mortyspd = ':warning:'
    else:
        mortyspd = str(mortyspd)

    embed = hikari.Embed(title='#' + str(mortynumber) + ' ' + mortyname + ' ' + mortyrarity + ' ' + mortytype,
                         color=(19, 252, 3),
                         description='**L.' + mortylevel + '**, HP:' + mortyHP + ', Atk:' +
                                     mortyatk + ', Def:' + mortydef + ', Spd:' + mortyspd + "\n\n"
                                     + message)

    if err_num:
        embed.set_thumbnail(
            'https://media.discordapp.net/attachments/1013921169415614507/1018045899789848576/000.png')
    else:
        embed.set_thumbnail(
            'https://pocketmortys.net/images/assets/' + mortydata['assetid'] + 'Down_1.png')

    embed.set_footer(
        "\n\n___\nNote: /predictivs relies on correct seed assumptions.\nUse at your own risk.")

    if True not in [err_num, err_level, err_HP, err_atk, err_def, err_spd] and False not in validstatslist:
        await ctx.respond(embed)
    else:
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)


@bot.command
@lightbulb.option("morty_spd", "morty speed stat", type=hikari.OptionType.INTEGER, required=False)
@lightbulb.option("morty_def", "morty defense stat", type=hikari.OptionType.INTEGER, required=False)
@lightbulb.option("morty_atk", "morty attack stat", type=hikari.OptionType.INTEGER, required=False)
@lightbulb.option("morty_hp", "morty hp stat", type=hikari.OptionType.INTEGER, required=False)
@lightbulb.option("morty_level", "morty level", type=hikari.OptionType.INTEGER, required=True)
@lightbulb.option("morty_number", "morty number", type=hikari.OptionType.INTEGER, required=False)
@lightbulb.option("screenshot", "stats page screenshot", type=hikari.OptionType.ATTACHMENT, required=False)
@lightbulb.command('ivs', 'Calculates Morty IVs from a stats page screenshot and/or given stats')
@lightbulb.implements(lightbulb.SlashCommand)
async def calcIVs(ctx: lightbulb.Context) -> None:
    if ctx.options.screenshot is not None:
        screenshot_input = ctx.options.screenshot
        media_type = screenshot_input.media_type
        if media_type is not None and 'image' in media_type:
            screenshot = bleach.clean(screenshot_input.url)
        else:
            screenshot = None
    else:
        screenshot = None

    er_message = ''
    err_level = False
    runpredict = False

    try:
        mortylevel = ctx.options.morty_level
        if mortylevel < 5 or mortylevel > 100:
            mortylevel = -1
            er_message = er_message + ':warning: morty_level must be an integer between 5 and 100.\n'
            err_level = True
    except:
        mortylevel = -1
        er_message = er_message + ':warning: morty_level must be an integer between 5 and 100.\n'
        err_level = True

    userinput = get_userinput(screenshot, ctx.options.morty_number,
                              ctx.options.morty_hp, ctx.options.morty_atk,
                              ctx.options.morty_def, ctx.options.morty_spd, mortylevel)

    er_message = er_message + userinput[0]
    mortynumber = userinput[1]
    mortyHP = userinput[2]
    mortyatk = userinput[3]
    mortydef = userinput[4]
    mortyspd = userinput[5]
    err_HP = userinput[6]
    err_atk = userinput[7]
    err_def = userinput[8]
    err_spd = userinput[9]
    err_num = userinput[10]

    if mortynumber == -1:
        mortydata = getmortydata(1)
    else:
        mortydata = getmortydata(mortynumber)
    mortyname = mortyEN_full['Morty'][mortydata['id']]['name']
    mortyHPbase = mortydata['hpbase']
    mortyatkbase = mortydata['attackbase']
    mortydefbase = mortydata['defencebase']
    mortyspdbase = mortydata['speedbase']

    mortytype = ""
    if mortydata['elementtype'] == "Rock":
        mortytype = rock
    elif mortydata['elementtype'] == "Paper":
        mortytype = paper
    elif mortydata['elementtype'] == "Scissors":
        mortytype = scissors

    mortyrarity = rarity[int(mortydata['division']) - 1]

    validstatslist = validstats(mortynumber, mortylevel, mortyHP, mortyatk, mortydef, mortyspd, mortyHPbase,
                                mortyatkbase, mortydefbase, mortyspdbase)

    if False in validstatslist and -1 not in [mortylevel, mortynumber]:
        if not validstatslist[0]:
            er_message += ':warning: The HP stat: ' + \
                          str(mortyHP) + ' is not possible.\n'
        if not validstatslist[1]:
            er_message += ':warning: The Atk stat: ' + \
                          str(mortyatk) + ' is not possible.\n'
        if not validstatslist[2]:
            er_message += ':warning: The Def stat: ' + \
                          str(mortydef) + ' is not possible.\n'
        if not validstatslist[3]:
            er_message += ':warning: The Spd stat: ' + \
                          str(mortyspd) + ' is not possible.\n'
        message = er_message
    elif mortylevel != -1 and mortynumber != -1 and (
            mortyHP != -1 or mortyatk != -1 or mortydef != -1 or mortyspd != -1):
        ivs0 = get_IVs(0, mortynumber, mortylevel, mortyHP, mortyatk, mortydef, mortyspd, mortyHPbase, mortyatkbase,
                       mortydefbase, mortyspdbase)
        ivs1 = get_IVs(1, mortynumber, mortylevel, mortyHP, mortyatk, mortydef, mortyspd, mortyHPbase, mortyatkbase,
                       mortydefbase, mortyspdbase)

        comment = ''

        if len(ivs0[0]) > 0 and len(ivs0[1]) > 0 and len(ivs0[2]) > 0 and len(ivs0[3]) > 0:
            if ivs0[0][0] == 16 or (ivs0[1][0] == 16 and ivs0[2][0] == 16 and ivs0[3][0] == 16):
                comment = "\n\n'Perfect'"
            elif ivs0[0][-1] >= 15 and ivs0[3][-1] == 16 and math.floor((ivs0[1][-1] + ivs0[2][-1] + 16) / 3) >= 15:
                comment = "\n\n'15/16'"
                if ivs0[0][-1] == 16 and ivs0[1][-1] == 16 and ivs0[2][-1] == 16 and ivs0 != [[16], [16], [16], [16]]:
                    comment = '\n\nPossible 16/16 - SEED IT!!'
                elif (ivs0[0][0] < 15 and math.floor((ivs0[1][0] + ivs0[2][0] + ivs0[3][0]) / 3) < 15) or ivs0[3][
                    0] < 16:
                    comment = '\n\nPossible 15/16 - SEED IT!!'
            elif ivs0[1:] == [[1], [1], [1]]:
                comment = "\n\n'Perfect Trash'"
        if len(ivs1[0]) > 0 and len(ivs1[1]) > 0 and len(ivs1[2]) > 0 and len(ivs1[3]) > 0:
            if ivs1[0][0] == 16 or (ivs1[1][0] == 16 and ivs1[2][0] == 16 and ivs1[3][0] == 16):
                comment = "\n\n'Perfect'"
            elif ivs1[0][-1] >= 15 and ivs1[3][-1] == 16 and math.floor((ivs1[1][-1] + ivs1[2][-1] + 16) / 3) >= 15:
                comment = "\n\n'15/16'"
                if ivs1[0][-1] == 16 and ivs1[1][-1] == 16 and ivs1[2][-1] == 16 and ivs1 != [[16], [16], [16], [16]]:
                    comment = '\n\nPossible 16/16 - SEED IT!!'
                elif (ivs1[0][0] < 15 and math.floor((ivs1[1][0] + ivs1[2][0] + ivs1[3][0]) / 3) < 15) or ivs1[3][
                    0] < 16:
                    comment = '\n\nPossible 15/16 - SEED IT!!'
            elif ivs1[1:] == [[1], [1], [1]]:
                comment = "\n\n'Perfect Trash'"

        if ivs0 != [[], [], [], []] and (
                ([] in ivs0) or math.floor((ivs0[1][0] + ivs0[2][0] + ivs0[3][0]) / 3) > ivs0[0][-1] or math.floor(
            (ivs0[1][-1] + ivs0[2][-1] + ivs0[3][-1]) / 3) < ivs0[0][0]):
            comment = '\n\n:warning: Invalid IVs - this Morty is partly trained and/or seeded. Running /predictivs with [0,0,0] seeds...'
            runpredict = True
        elif ivs0 == [[], [], [], []] and ivs1 == [[], [], [], []]:
            comment = '\n\n:warning: Invalid IVs - this Morty is partly trained and/or seeded. Running /predictivs with [0,0,0] seeds...'
            runpredict = True
        if ivs1 != [[], [], [], []] and (
                ([] in ivs1) or math.floor((ivs1[1][0] + ivs1[2][0] + ivs1[3][0]) / 3) > ivs1[0][-1] or math.floor(
            (ivs1[1][-1] + ivs1[2][-1] + ivs1[3][-1]) / 3) < ivs1[0][0]):
            comment = "\n\n:warning: Invalid IVs - this Morty isn't fully EVd. Running /predictivs with [0,0,0] seeds..."
            runpredict = True

        if err_HP or err_atk or err_def or err_spd:
            comment = '\n\n' + er_message

        message = 'IVs (if 0 EVs): ' + format_IVs(ivs0, err_HP, err_atk, err_def, err_spd) + '\n' \
                  + 'IVs (if max EVs): ' + format_IVs(ivs1, err_HP,
                                                      err_atk, err_def, err_spd) + comment

    else:
        message = er_message

    if mortynumber == -1:
        mortyname = "morty_name"

    if mortynumber == 422 and mortylevel == 100 and (mortyatk > 343 or mortydef > 353):
        mortyname = '(OG) ' + mortyname

    if err_level:
        mortylevel = ':warning:'
    else:
        mortylevel = str(mortylevel)
    if err_HP:
        mortyHP = ':warning:'
    else:
        mortyHP = str(mortyHP)
    if err_atk:
        mortyatk = ':warning:'
    else:
        mortyatk = str(mortyatk)
    if err_def:
        mortydef = ':warning:'
    else:
        mortydef = str(mortydef)
    if err_spd:
        mortyspd = ':warning:'
    else:
        mortyspd = str(mortyspd)

    embed = hikari.Embed(title='#' + str(mortynumber) + ' ' + mortyname + ' ' + mortyrarity + ' ' + mortytype,
                         color=(27, 86, 204),
                         description='**L.' + mortylevel + '**, HP:' + mortyHP + ', Atk:' +
                                     mortyatk + ', Def:' + mortydef + ', Spd:' + mortyspd + "\n\n"
                                     + message)

    if err_num:
        embed.set_thumbnail(
            'https://media.discordapp.net/attachments/1013921169415614507/1018045899789848576/000.png')
    else:
        embed.set_thumbnail(
            'https://pocketmortys.net/images/assets/' + mortydata['assetid'] + 'Down_1.png')

    embed.set_footer("")

    if not err_num and not err_level and [err_HP, err_atk, err_def, err_spd] != [True, True, True,
                                                                                 True] and False not in validstatslist:
        await ctx.respond(embed)
    else:
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    if runpredict:
        await predictIVs(ctx)


bot.run()