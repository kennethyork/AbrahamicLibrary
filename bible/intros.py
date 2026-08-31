"""Plain-language introductions to the hardest books in the volume.

Four of the works here are Greek histories and arguments — 2 Maccabees,
1 Esdras, 3 Maccabees and 4 Maccabees. They are harder going than anything
else in the book, and not mainly because of the translation. They are hard
because a reader is dropped into Seleucid court politics with no idea who
anyone is, and because their sentences were built for an audience trained in
Greek rhetoric.

The text itself is left exactly as the translators made it. What is added
here is a page of orientation before each one: who the people are, what is
happening and why, what to expect from the way it is written, and where the
hard parts are. These are written for this edition, in plain language, and
quote nothing.
"""

# book running-head -> introduction paragraphs
INTROS = {
 '2 Maccabees': [
  'Before you start. This is the hardest book in this volume to read, and it '
  'helps to know why before you begin. It is not a sequel to 1 Maccabees. It '
  'is a separate account of some of the same events, written in Greek by '
  'someone who says he is condensing a five-volume history by a man named '
  'Jason of Cyrene. He tells you that himself, and he apologizes for the '
  'work it cost him.',

  'The politics in one paragraph. Judea is a small province caught between '
  'two Greek empires left over from Alexander the Great. The one that matters '
  'here is the Seleucid empire, ruled from Antioch in Syria. Its kings appear '
  'throughout: Seleucus, then Antiochus Epiphanes, then Antiochus Eupator, '
  'then Demetrius. The Jewish high priesthood has become a job the king sells '
  'to the highest bidder, which is what starts the trouble. Jason buys it '
  'from his brother Onias. Menelaus then outbids Jason. Each of them is '
  'willing to make Jerusalem more Greek to keep the post.',

  'What happens. The temple treasury is raided. The high priesthood is bought '
  'and sold. Antiochus loots the temple, bans the Jewish religion, and turns '
  'the sanctuary over to another god. People are tortured and killed for '
  'refusing to eat pork or to break the sabbath — including an old scribe '
  'named Eleazar, and a mother with seven sons, whose deaths take up two of '
  'the most famous chapters in the book. Judas Maccabeus raises a revolt, '
  'wins a string of battles, and cleanses the temple. The book ends with the '
  'defeat of a general named Nicanor, and a holiday to mark it.',

  'How it is written. The author is not writing plain chronicle. He is '
  'writing to move you, and he uses every tool he has: heavenly horsemen in '
  'gold armor, villains who die of worms, speeches at the point of death. '
  'Sentences run long because that was considered good Greek. If you lose the '
  'thread of one, the trick is to read to the next full stop and keep going; '
  'the story does not depend on catching every clause.',

  'What to watch for. Two ideas appear here that appear nowhere earlier in '
  'the Bible, and they are why this book mattered so much later: the '
  'resurrection of the body, said plainly by the dying brothers, and prayer '
  'and offerings for the dead, at the very end.',
 ],
 '1 Esdras': [
  'Before you start. This book covers ground you may already know. It retells '
  'the story found in Ezra, parts of 2 Chronicles, and part of Nehemiah — the '
  'end of the kingdom of Judah, the exile to Babylon, and the return to '
  'rebuild the temple. If a passage feels familiar, that is why.',

  'It is not a straight copy. The order of events is different, some material '
  'is missing, and one long episode appears here and nowhere else. That '
  'episode is the reason most people read the book, and it comes in the third '
  'and fourth chapters.',

  'The famous part. Three young bodyguards of the Persian king hold a contest '
  'while he sleeps. Each writes down what he thinks is the strongest thing in '
  'the world, and the winner is to be richly rewarded. The first says wine. '
  'The second says the king. The third, Zerubbabel, says women — and then '
  'says that truth is stronger than any of them, and wins. His prize is '
  'permission to rebuild Jerusalem.',

  'What makes it hard. The book is full of lists — of families who returned, '
  'of who gave what, of who had married foreign wives — and of Persian '
  'officials with unfamiliar names writing letters to each other. The letters '
  'are formal and long, because that is how imperial correspondence sounded. '
  'You can read the lists quickly without losing the story.',

  'A note on the name. The Greek for Ezra is Esdras, so this book and the '
  'biblical Ezra share a name and much of their content. In some editions '
  'this book is called 3 Esdras instead. The 2 Esdras printed elsewhere in '
  'this volume is a completely different work.',
 ],
 '3 Maccabees': [
  'Before you start. Despite the name, this book has nothing to do with the '
  'Maccabees. It contains no Maccabee, and it happens about fifty years '
  'before the revolt they led. The title is a later accident of how these '
  'books were bound together.',

  'Where and when. Egypt, under King Ptolemy the Fourth. The Jewish community '
  'there is large, long settled, and mostly getting on fine — which is what '
  'makes the story work.',

  'What happens. The king wins a battle, tours the region, and decides to '
  'enter the sanctuary in Jerusalem. He is told he cannot. He insists, is '
  'struck down before he can, and goes home humiliated and angry. He takes it '
  'out on the Jews of Egypt: first by stripping their legal status, then by '
  'ordering the entire community rounded up in the hippodrome at Alexandria '
  'to be trampled by five hundred elephants drugged with wine and incense.',

  'How it turns. The plan fails three times, each more absurd than the last. '
  'The king oversleeps. Then he forgets his own order. Then the elephants '
  'turn on his own troops. He changes his mind completely, throws a seven-day '
  'feast for the people he meant to kill, and writes a letter praising them.',

  'How it is written. This is the most extravagant writing in the volume. The '
  'prayers are long, the adjectives are piled up, and the author never uses '
  'one word where four will do. That is deliberate — it is a story about '
  'rescue at the last possible moment, told to be read aloud at a festival. '
  'Read it for the shape of the story rather than the detail of the '
  'sentences.',
 ],
 '4 Maccabees': [
  'Before you start. This is not a history. It is a lecture, and it says so '
  'in its first sentence. The question it sets out to answer is whether '
  'religious reason can master the feelings — appetite, anger, fear, pain — '
  'and it argues the case the way a Greek philosopher would, with a thesis, '
  'evidence and a conclusion.',

  'Where the evidence comes from. The examples are taken from 2 Maccabees, '
  'printed earlier in this volume: the old scribe Eleazar, and the mother '
  'with seven sons, all tortured and killed under Antiochus for refusing to '
  'break their law. If you have read that book, you already know these '
  'people. Here their deaths are not narrated so much as examined, as proof '
  'that reason held when the body could not.',

  'What makes it hard. Two things. The first is the vocabulary of Greek '
  'philosophy — the four cardinal virtues, the passions, the idea of reason '
  'as a ruler over the mind — which the author expects you to know. The '
  'second is that the torture scenes are described at length and in detail, '
  'and are meant to be almost unbearable. That is the argument: the worse the '
  'pain, the stronger the proof.',

  'How to read it. Follow the argument rather than the sentences. The '
  'structure is simple even when the wording is not. He states his case, '
  'defines his terms, gives his examples one after another, and then sums up. '
  'The opening and closing chapters carry the argument; the middle carries '
  'the evidence.',

  'Why it survived. Early Christian writers valued this book for its picture '
  'of dying rather than betraying a conviction, and it shaped how the deaths '
  'of the martyrs were later described. Several of the Apostolic Fathers '
  'printed later in this volume are working with the same idea.',
 ],
}

# --- The Apostolic Fathers ------------------------------------------------
#
# The largest block of hard reading in the volume: ninety-six thousand words
# at about the eleventh grade, and two pieces above the fifteenth. The
# difficulty is the same as the Greek histories — long argued sentences, and
# a reader who has no idea who these people were or why they were writing.
INTROS.update({
 'Didache': [
  'Before you start. This is probably the oldest Christian writing outside '
  'the New Testament, and it is the plainest thing in this division. It is '
  'not a letter or an argument. It is a manual — how to live, how to baptize, '
  'how to pray, how to run a meal, and how to handle visiting preachers.',
  'How it was found. It was lost for something like fourteen hundred years. A '
  'bishop found the only complete copy in a library in Constantinople in '
  '1873, bound in with other texts. That is three years after the volume most '
  'of this division comes from went to press, which is why the Didache is '
  'translated here from a later edition of the same series.',
  'What to look for. The first six chapters set out two roads, one of life '
  'and one of death, and list what belongs to each. Then come practical '
  'instructions: baptize in running water if you can, and if you cannot, pour '
  'water on the head three times. Fast on Wednesday and Friday rather than '
  'Monday and Thursday, so as not to fast with the hypocrites. Say the '
  'Lord’s Prayer three times a day. And there are rules for testing a '
  'traveling prophet, which are wonderfully blunt: if he stays three days, or '
  'asks for money, he is a fraud.',
 ],
 '1 Clement': [
  'Before you start. A letter from the church at Rome to the church at '
  'Corinth, written about sixty years after Paul wrote to the same city, and '
  'about the same problem. It is the longest and most important thing in this '
  'division, and the oldest Christian document outside the New Testament that '
  'we can date with any confidence.',
  'The situation. The Corinthians have thrown out their elders. Nobody says '
  'the elders did anything wrong; a younger faction simply removed them. Rome '
  'writes to say that this is not how a church should behave, and spends '
  'twelve thousand words saying it.',
  'Why it goes on so long. Clement argues the way a trained Roman would. He '
  'does not simply tell them to stop. He builds a case from every direction: '
  'from the Old Testament, from the natural order, from the discipline of the '
  'Roman army, from the way a body needs all its parts. He gives long lists '
  'of examples of jealousy causing harm, beginning with Cain. He includes a '
  'passage about the phoenix rising from its own ashes as an argument for '
  'resurrection, which readers still remark on.',
  'What to watch for. He describes Peter and Paul as men of his own recent '
  'past, which is the closest thing we have to a contemporary notice of their '
  'deaths. And he takes for granted a structure of bishops and deacons '
  'appointed in an orderly succession, which is why this letter has been '
  'argued over ever since.',
 ],
 '2 Clement': [
  'Before you start. Two things about the title are wrong. It is not by '
  'Clement, and it is not a letter. It is a sermon — the oldest Christian '
  'sermon that survives — and at one point the speaker refers to reading it '
  'aloud to a congregation while they listen.',
  'What it is about. Repentance, and the shortness of the time left to do it '
  'in. The argument is that being saved cost a great deal, so the response '
  'has to be a changed life rather than words. It is more urgent and less '
  'organized than 1 Clement, which is what you would expect from something '
  'spoken.',
  'What to watch for. It quotes sayings of Jesus that are not in our gospels, '
  'and it quotes a lost writing called the Gospel of the Egyptians. Those '
  'quotations are the reason scholars read it closely.',
 ],
 'Polycarp': [
  'Before you start. Polycarp was bishop of Smyrna, and he is the bridge '
  'between the apostles and the second century. Irenaeus, who knew him as a '
  'boy, says Polycarp had been taught by the apostle John. He died about the '
  'year 155, very old.',
  'The letter. He writes to the church at Philippi, the same congregation '
  'Paul wrote to, and he knows it — he says so, and tells them he cannot '
  'match Paul. They had asked him for copies of Ignatius’ letters, which is '
  'how we know those letters were being collected almost at once.',
  'Why it is hard going. It is short but dense, and it is stitched together '
  'almost entirely out of quotations from Paul, Peter and the gospels, run '
  'one into another without a break. Reading it feels like hearing someone '
  'who has memorized the New Testament think out loud in its words.',
  'The awkward part. A presbyter named Valens and his wife have been caught '
  'in some financial dishonesty. Polycarp deals with it briefly and with more '
  'grief than anger, and asks the congregation to be moderate.',
 ],
 'Martyrdom of Polycarp': [
  'Before you start. This is the oldest surviving account of a Christian '
  'death outside the New Testament, written as a letter from the church at '
  'Smyrna to another congregation, by people who say they were there.',
  'What happens. Polycarp is hunted, refuses to run twice, and is finally '
  'taken while praying at a farmhouse. He asks his captors for an hour to '
  'pray and takes two. At the stadium the governor presses him to swear by '
  'the emperor and curse Christ, and offers him every chance to escape. He '
  'refuses, saying he has served Christ eighty-six years and cannot deny him '
  'now. He is burned, and then stabbed when the fire does not do it.',
  'Why it reads oddly. It is the hardest writing in this division to follow, '
  'and the reason is that it was written to be read aloud in worship. The '
  'sentences are formal and heightened, and the deliberate parallels to the '
  'death of Jesus — the betrayal, the entry into the city, the crowd — are '
  'part of the point rather than an accident.',
  'What to watch for. The care the writers take at the end to say that they '
  'worship Christ and only honor the martyrs. That distinction is being drawn '
  'here for the first time.',
 ],
 'Barnabas': [
  'Before you start. Not by Barnabas, the companion of Paul, though it '
  'circulated under his name and was treated as scripture in some places. The '
  'author is unknown and was probably writing in Alexandria.',
  'The argument, which is uncomfortable. He holds that the Jewish law was '
  'never meant to be kept literally — that the food laws, the sacrifices, the '
  'sabbath and the temple were always pictures of something else, and that '
  'Israel misunderstood its own scriptures from the beginning. This is the '
  'harshest thing in the volume on that subject, and it should be read '
  'knowing what it is.',
  'How he reads. Everything is a figure of something. The animals forbidden '
  'as food stand for kinds of people to avoid. The three hundred and eighteen '
  'servants of Abraham become a coded reference to the cross. He is doing '
  'what Alexandrian readers did with Homer, applied to the Bible.',
  'What to watch for. The last four chapters are a version of the Two Ways — '
  'the same material found at the start of the Didache — which suggests both '
  'are drawing on something older that neither of them invented.',
 ],
 'Ignatius to the Ephesians': [
  'Before you start these seven letters. Ignatius was bishop of Antioch in '
  'Syria. Some time around the year 110 he was arrested, condemned, and sent '
  'to Rome under guard to be killed by animals in the arena. He wrote seven '
  'letters on that journey, chained to ten soldiers he describes as leopards '
  'who only get worse when treated kindly. He knew exactly where he was '
  'going, and he wrote fast.',
  'That is why they read as they do. They are urgent, broken, and repetitive '
  'in places, and they lurch between subjects. He is not composing at a desk. '
  'Four were written from Smyrna and three from Troas, and the same three '
  'concerns run through all of them: hold together, stay with your bishop, '
  'and do not try to save me.',
  'This letter. The longest and most carefully written of the seven, sent to '
  'the church that had already received a letter from Paul. Its subject is '
  'unity — he compares the congregation to a choir singing in tune — and it '
  'contains his warning about people who carry the name of Christ and act '
  'against it.',
 ],
 'Ignatius to the Magnesians': [
  'Their bishop is young, and some are evidently taking advantage of it. '
  'Ignatius tells them to respect him anyway and not to presume on his age. '
  'The letter also argues against keeping the sabbath in the old manner, and '
  'is among the earliest writings to give a reason for meeting on Sunday. It '
  'is one of the more tightly argued of the seven, which makes it slower '
  'going than the others.',
 ],
 'Ignatius to the Trallians': [
  'A short letter, mostly a warning against people who say Christ only '
  'appeared to have a body and only appeared to suffer. Ignatius answers by '
  'listing what actually happened, and by pointing out that if it was all an '
  'appearance then his own chains are pointless. He also says, with some '
  'charm, that he could write about heavenly things but will not, because '
  'they are not ready and neither is he.',
 ],
 'Ignatius to the Romans': [
  'The most famous of the seven, and the most personal. It is the one letter '
  'in which he asks for nothing practical. He begs the Roman Christians not '
  'to use their influence to have him spared, and the language he uses about '
  'his coming death is so intense that it has disturbed readers ever since — '
  'he asks to be ground like wheat by the teeth of the animals. Read alone it '
  'sounds like a man in love with dying. Read alongside the other six, in '
  'which he spends his last weeks worrying about other people’s '
  'congregations, it reads differently.',
 ],
 'Ignatius to the Philadelphians': [
  'Written after passing through their city, where something went wrong. He '
  'refers to standing up in a meeting and calling out in a loud voice for '
  'them to stay with their bishop, and to being accused afterward of having '
  'been tipped off about their divisions in advance. He denies it. The letter '
  'also records an argument he had with people who would not accept anything '
  'unless they could find it in the Old Testament.',
 ],
 'Ignatius to the Smyrnaeans': [
  'Two things make this one notable. It contains the first known use of the '
  'phrase catholic church, meaning the whole church rather than a party '
  'within it. And it argues hardest of all seven that Christ was genuinely '
  'flesh and blood — that he really ate and drank after rising, and was not a '
  'spirit. Ignatius says plainly that if that is not true, then he is dying '
  'for nothing.',
 ],
 'Ignatius to Polycarp': [
  'The only one of the seven written to a person rather than a congregation, '
  'and the easiest to read. It is an older man’s advice to a younger bishop '
  'he has just met, and it is almost entirely practical: stand firm, be '
  'patient with difficult people, do not neglect the widows, do not let '
  'anything be done without you, and do not be thrown by people who seem '
  'trustworthy and teach strange things. It ends with instructions about the '
  'married and about slaves.',
 ],
 'Syriac Ignatius': [
  'A shorter version of three of the letters — to Polycarp, to the Ephesians '
  'and to the Romans — preserved in Syriac rather than Greek. For much of the '
  'nineteenth century scholars argued about whether this short version was '
  'the original and the longer Greek text an expansion. That argument is now '
  'settled the other way, but the Syriac text is printed here because the '
  'volume this division comes from printed it, and because comparing the two '
  'is instructive.',
 ],
 'Martyrdom of Ignatius': [
  'Before you start. This is the single hardest piece of writing in the '
  'volume, and you should know that before you begin rather than conclude '
  'something is wrong with you. Its sentences are the longest here and its '
  'vocabulary the heaviest.',
  'What it is. An account of Ignatius being brought to Rome and killed, told '
  'by people claiming to have traveled with him. It is much later than the '
  'letters and is not reliable history, and it was written in the elevated '
  'style used for such accounts rather than as a report.',
  'How to read it. The story is simple even when the sentences are not: he is '
  'brought before the emperor Trajan, argues with him, is condemned, sails to '
  'Rome, is killed in the amphitheater, and the harder bones are gathered up '
  'and carried back to Antioch. If a sentence defeats you, go to the next '
  'full stop. You will not lose the thread.',
 ],
 'Diognetus': [
  'Before you start. The most attractive writing in this division, and the '
  'most mysterious. Nobody knows who wrote it, when, or who Diognetus was. '
  'The only manuscript was found in a fish shop in Constantinople, used as '
  'wrapping paper, and it was destroyed by fire in Strasbourg in 1870, so '
  'every printed text depends on copies made before that.',
  'What it is. A letter to an educated pagan who has asked genuine questions '
  'about this new religion: why Christians do not worship the old gods, why '
  'they do not keep Jewish customs, why they love each other, and why the '
  'whole thing appeared so recently.',
  'The famous passage. The answer to the first question includes a '
  'description of Christians as living in their own countries as resident '
  'foreigners — obeying the laws, and living above them — and a comparison of '
  'their place in the world to the soul’s place in the body. That passage '
  'has been quoted for eighteen centuries.',
  'Note. The last two chapters are in a different voice and are generally '
  'thought to be by someone else, tacked on later.',
 ],
 'Hermas': [
  'Before you start. This is the longest work in the volume — nearly forty '
  'thousand words, longer than any book of the Bible except Psalms and '
  'Jeremiah — so it helps to know the shape of it in advance.',
  'Who Hermas was. He tells us: a former slave in Rome, freed, who went into '
  'business, did badly, and had a family who went wrong during a persecution. '
  'The book is his, and the domestic detail is unusually vivid for the '
  'period.',
  'The shape. Three parts, and they are quite different from each other. '
  'First the Visions, in which an old woman appears to him — she turns out to '
  'be the church — and shows him a tower being built out of stones, some of '
  'which are rejected. Then the Mandates, twelve short commandments on '
  'ordinary matters: truthfulness, purity, patience, cheerfulness, trust, and '
  'the danger of being of two minds. Then the Similitudes, ten longer '
  'picture-stories, of which the willow tree and the elm and the vine are the '
  'best known.',
  'What the argument is. One question runs underneath all of it: whether a '
  'Christian who sins seriously after baptism can be forgiven. Hermas answers '
  'that there is one more chance, and only one, and that it will not be open '
  'forever. That answer was controversial then and shaped how the church '
  'handled penance for centuries.',
  'How to read it. Do not read it straight through. The Mandates stand alone '
  'and are the easiest part. The Visions repay reading in order. The '
  'Similitudes can be taken one at a time.',
 ],
 'Papias': [
  'Before you start. There is no book here. Papias wrote five volumes of '
  'explanations of the sayings of Jesus early in the second century, and all '
  'five are lost. What survives are quotations of him by later writers, '
  'mostly Irenaeus and Eusebius, gathered up and printed together — so this '
  'reads as a series of disconnected fragments, because that is what it is.',
  'Why he matters anyway. Two of these fragments are among the most argued '
  'over sentences in early Christian literature. In one, Papias says Mark '
  'wrote down accurately what he remembered of Peter’s preaching, though not '
  'in order. In another, he says Matthew compiled the sayings in the Hebrew '
  'language. Those two remarks are the oldest evidence we have about how the '
  'gospels came to be written.',
  'A word about the man. He says he preferred asking people who had known the '
  'apostles to reading books, because he thought a living voice was worth '
  'more. Eusebius, who preserved much of what we have, also thought he was '
  'not very bright, and said so.',
 ],
})
