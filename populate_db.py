import requests
import time
import os
import shutil
from sqlalchemy.orm import Session
# from main import SessionLocal, Prompt, Submission, Vote, Tag, Favorite - Moved inside populate()

USER_ORACLE = "the_oracle"

DATA = [
    {
        "title": "Power Playbooks",
        "description": "The definitive guides on understanding, acquiring, and wielding power in political, social, and control structures.",
        "books": [
            {
                "query": "The Power Broker Robert Caro",
                "justification": "Robert Caro's masterpiece is not just a biography of Robert Moses; it is the ultimate textbook on how political power is accumulated and used to reshape the physical world, often at the expense of the disenfranchised. It reveals the mechanics of modern bureaucracy and hidden influence.",
                "tags": ["Biography", "Politics", "Urban Planning", "Bureaucracy"]
            },
            {
                "query": "The Dictator's Handbook Bruce Bueno de Mesquita",
                "justification": "This book strips away ideology to reveal the raw logic of political survival. It explains that leaders do not act for the 'good of the people' but to satisfy their essential coalition. It provides a chillingly rational framework for understanding everything from corporate boards to autocracies.",
                "tags": ["Game Theory", "Political Science", "Realpolitik"]
            },
            {
                "query": "The Prince Niccolo Machiavelli",
                "justification": "The original treatise on realpolitik. Machiavelli's work remains indispensible because it dares to separate ethics from effectiveness. It forces the reader to confront the uncomfortable truths about what it takes to maintain stability and authority in a chaotic world.",
                "tags": ["Philosophy", "Classics", "Strategy", "Statecraft"]
            },
            {
                "query": "On Power Bertrand de Jouvenel",
                "justification": "A deep historical and philosophical analysis of the nature of power itself—not just who holds it, but how the apparatus of the state naturally expands. Jouvenel traces the growth of power from feudalism to modern democracy, warning of its inherent tendency to centralize.",
                "tags": ["Political Philosophy", "History", "Sovereignty"]
            },
            {
                "query": "New Power Jeremy Heimans",
                "justification": "A modern counterpoint to the 'old power' of held authority. Heimans and Timms conceptualize 'new power' as a current made by many—open, participatory, and peer-driven (like #MeToo or Bitcoin). Understanding the conflict and fusion between these two models is essential for modern leadership.",
                "tags": ["Sociology", "Technology", "Social Movements"]
            }
        ]
    },
    {
        "title": "Managing Complex Projects",
        "description": "Books that save you from the tar pit. Systems engineering, management science, and the psychology of getting big things done.",
        "books": [
            {
                "query": "The Mythical Man-Month Fred Brooks",
                "justification": "The foundational text of software engineering that applies to all complex systems. Brooks's Law—adding manpower to a late project makes it later—is a counter-intuitive truth that every manager must internalize. It captures the essence of communication overhead and the limits of parallelization.",
                "tags": ["Software Engineering", "Management", "Classics", "Systems Thinking"]
            },
            {
                "query": "Systems Engineering: Coping with Complexity Richard Stevens",
                "justification": "This is the rigorous handbook for the discipline of Systems Engineering. It moves beyond 'management' into the technical structuring of requirements, interfaces, and verification. Essential for anyone building physical products, aerospace systems, or large-scale infrastructure.",
                "tags": ["Engineering", "Textbook", "Process", "Architecture"]
            },
            {
                "query": "Thinking in Systems Donella Meadows",
                "justification": "Meadows provides the mental models needed to identify feedback loops, leverage points, and non-linear behaviors in complex systems. It helps project managers see beyond the Gantt chart to the underlying dynamics that cause projects to oscillate or collapse.",
                "tags": ["Systems Thinking", "Sustainability", "Mental Models"]
            },
            {
                "query": "High Output Management Andrew Grove",
                "justification": "Andy Grove applied the principles of manufacturing production—leverage, bottlenecks, quality control—to the 'soft' world of management. It remains the best guide on how to structure an organization to maximize the output of its teams, treating management itself as a high-leverage activity.",
                "tags": ["Business", "Leadership", "Productivity", "Intel"]
            },
            {
                "query": "Normal Accidents Charles Perrow",
                "justification": "Perrow argues that in tightly coupled, complex systems, accidents are inevitable (or 'normal'). For project managers, this is a crucial lesson in risk: you cannot eliminate failure, you must design for resilience and decoupling. A sobering look at nuclear plants, shipping, and genetics.",
                "tags": ["Risk Management", "Sociology", "Safety", "Complexity"]
            }
        ]
    },
    {
        "title": "Designing Effective Cities",
        "description": "Urban planning, architecture, and the sociology of how we live together. Moving beyond aesthetics to function and human flourishing.",
        "books": [
            {
                "query": "The Death and Life of Great American Cities Jane Jacobs",
                "justification": "Jacobs single-handedly overturned the modernist dogma of top-down city planning. She championed the 'ballet of the sidewalk,' mixed-use neighborhoods, and density. Her observations on safety, eyes on the street, and organic urban growth are the bedrock of human-centric urbanism.",
                "tags": ["Urban Planning", "Sociology", "Architecture", "Classics"]
            },
            {
                "query": "A Pattern Language Christopher Alexander",
                "justification": "A monumental catalog of 253 patterns that describe deep problems in design and their solutions. From 'Agricultural Valleys' to 'Light on Two Sides of Every Room,' it offers a vocabulary for building environments that feel alive and support human well-being at every scale.",
                "tags": ["Architecture", "Design", "Philosophy", "Patterns"]
            },
            {
                "query": "Walkable City Jeff Speck",
                "justification": "Speck provides a practical, pragmatic manifesto for liberating cities from the car. He argues that walkability is not just an amenity but the central driver of economic competitiveness, public health, and environmental sustainability. A toolkit for modern mayors and planners.",
                "tags": ["Urban Design", "Transportation", "Sustainability", "Economics"]
            },
            {
                "query": "The City in History Lewis Mumford",
                "justification": "A sweeping historical survey of the city's role in civilization. Mumford traces the evolution of urban forms from the neolithic village to the modern megalopolis. It provides the deep context needed to understand the spiritual and cultural functions of the city, not just its mechanical ones.",
                "tags": ["History", "Civilization", "Sociology"]
            },
            {
                "query": "Happy City Charles Montgomery",
                "justification": "Montgomery connects urban design directly to the science of happiness. He uses psychology and neuroscience to show how suburbs breed anxiety and isolation, while well-designed dense cities foster trust and joy. It reframes the goal of city building from efficiency to emotional wellbeing.",
                "tags": ["Psychology", "Urban Planning", "Wellbeing", "Design"]
            }
        ]
    },
    {
        "title": "How Institutions Fail",
        "description": "From organizational rot to systemic collapse. Understanding why competent people build broken systems.",
        "books": [
            {
                "query": "Seeing Like a State James C. Scott",
                "justification": "Scott explains the failures of 'high modernism'—the state's attempt to make society legible and controllable. From scientific forestry to collectivization, he shows how simplifying complex, engaging realities for the sake of administrative convenience leads to disastrous fragility and failure.",
                "tags": ["Political Science", "Sociology", "Anarchism", "Complexity"]
            },
            {
                "query": "The Collapse of Complex Societies Joseph Tainter",
                "justification": "Tainter argues that societies collapse not because of specific catastrophes, but because of diminishing returns on complexity. As institutions solve problems, they add layers of cost/bureaucracy until the cost of maintaining the status quo exceeds the benefit, making collapse the rational economic outcome.",
                "tags": ["History", "Anthropology", "Economics", "Collapse"]
            },
            {
                "query": "Why Nations Fail Daron Acemoglu",
                "justification": "Acemoglu and Robinson posit that the key differentiator between rich and poor nations is institutions. 'Inclusive' institutions encourage participation and innovation, while 'extractive' institutions concentrate power and wealth, inevitably leading to stagnation and failure.",
                "tags": ["Economics", "History", "Development", "Politics"]
            },
            {
                "query": "Moral Mazes Robert Jackall",
                "justification": "A terrifying sociological study of corporate bureaucracy. Jackall shows how the internal structure of corporations separates actions from consequences, creating a feudal world where 'looking good' and pleasing the boss replace ethical behavior and competency. Essential for understanding corporate rot.",
                "tags": ["Sociology", "Business", "Ethics", "Bureaucracy"]
            },
            {
                "query": "Command and Control Eric Schlosser",
                "justification": "Through the lens of America's nuclear arsenal, Schlosser exposes the illusion of safety in complex, high-stakes organizations. It is a harrowing case study in how potential catastrophe is normalized and how systems designed to be foolproof are often fooled by human error and administrative blindness.",
                "tags": ["History", "Military", "Safety", "Technology"]
            }
        ]
    },
    {
        "title": "Corporate Capture and Market Abuse",
        "description": "Analyzing monopoly power, regulatory capture, and the distortion of free markets.",
        "books": [
            {
                "query": "Goliath Matt Stoller",
                "justification": "Stoller revives the history of the anti-monopoly movement in America. He traces how a shift in legal philosophy in the 1970s allowed power to consolidate in the hands of a few corporate giants, dismantling the democratic checks that once kept commerce in service to the public.",
                "tags": ["History", "Economics", "Politics", "Monopoly"]
            },
            {
                "query": "Dark Money Jane Mayer",
                "justification": "Mayer meticulously documents how a small network of ultra-wealthy families weaponized philanthropy and political funding to capture the American political system. It is the definitive account of the privatized machinery used to reshape laws and public opinion behind closed doors.",
                "tags": ["Journalism", "Politics", "Inequality"]
            },
            {
                "query": "Private Government Elizabeth Anderson",
                "justification": "Anderson challenges the idea that the 'free market' brings freedom to workers. She argues that modern corporations are actually private authoritarian governments, dictating the lives of employees with little accountability. A philosophical reimagining of workplace rights.",
                "tags": ["Philosophy", "Economics", "Labor", "Politics"]
            },
            {
                "query": "Merchants of Doubt Naomi Oreskes",
                "justification": "This book exposes the 'tobacco playbook'—the strategy of manufacturing scientific controversy to delay regulation. Oreskes and Conway show how the same group of scientists and lobbyists moved from defending smoking to denying acid rain and climate change, hacking the media's desire for 'balance.'",
                "tags": ["History of Science", "Politics", "Environment", "Media"]
            },
            {
                "query": "Treasure Islands Nicholas Shaxson",
                "justification": "An investigation into the shadow world of tax havens. Shaxson reveals that offshore finance isn't a fringe activity but the core of the global economic system, allowing corporations and elites to opt out of the social contract while extracting wealth from sovereign nations.",
                "tags": ["Economics", "Finance", "Globalism", "Corruption"]
            }
        ]
    },
    {
        "title": "How the Universe Works",
        "description": "The best high-level physics and cosmology books that don't talk down to you. Reality, time, and the fundamental nature of things.",
        "books": [
            {
                "query": "The Road to Reality Roger Penrose",
                "justification": "This is not a 'pop science' book; it is a complete guide to the physical universe for the dedicated reader. Penrose does not shy away from the mathematics, offering the most comprehensive and honest tour of modern physics, from geometry to quantum field theory.",
                "tags": ["Physics", "Mathematics", "Textbook", "Cosmology"]
            },
            {
                "query": "The Fabric of Reality David Deutsch",
                "justification": "Deutsch weaves together four strands—quantum physics, evolution, computation, and epistemology—into a unified Theory of Everything. His 'Many Worlds' interpretation is bold, but his defense of objective truth and progress is even more profound.",
                "tags": ["Philosophy", "Physics", "Science", "Epistemology"]
            },
            {
                "query": "QED Richard Feynman",
                "justification": "Feynman was the master explainer. In this series of lectures, he explains Quantum Electrodynamics (the interaction of light and matter) with zero analogies and zero confusion. He offers the 'strange theory' as it actually is, accessible to the layman without dumbing it down.",
                "tags": ["Physics", "Science", "Lectures", "Classic"]
            },
            {
                "query": "Order Out of Chaos Ilya Prigogine",
                "justification": "Prigogine, a Nobel laureate, explores non-equilibrium thermodynamics. He challenges the Newtonian view of a clockwork universe, showing how instability and time-irreversibility are the sources of order and life. A bridge between hard science and philosophy.",
                "tags": ["Chemistry", "Philosophy", "Thermodynamics", "Complexity"]
            },
            {
                "query": "Something Deeply Hidden Sean Carroll",
                "justification": "Carroll tackles the crisis at the heart of quantum mechanics: we know the math works, but we don't know what it means. He champions the 'Many Worlds' formulation as the only logical conclusion, providing a lucid guide to quantum entanglement and the nature of spacetime.",
                "tags": ["Physics", "Quantum Mechanics", "Cosmology"]
            }
        ]
    },
    {
        "title": "Creating Public Good",
        "description": "How to design effectively for the benefit of all. Philanthropy, non-profits, and systemic interventions.",
        "books": [
            {
                "query": "Doing Good Better William MacAskill",
                "justification": "The manifesto of Effective Altruism. MacAskill argues that reason and evidence should guide our philanthropy, not just empathy. By quantifying impact, we can do hundreds of times more good with the same resources. Essential for anyone wanting to maximize their positive footprint.",
                "tags": ["Ethics", "Philanthropy", "Philosophy", "Economics"]
            },
            {
                "query": "Governing the Commons Elinor Ostrom",
                "justification": "Ostrom won the Nobel Prize for disproving the 'Tragedy of the Commons.' She researched real-world communities that successfully manage shared resources (forests, fisheries) without state control or privatization, outlining the design principles for sustainable self-governance.",
                "tags": ["Economics", "Political Science", "Sustainability", "Game Theory"]
            },
            {
                "query": "The Life You Can Save Peter Singer",
                "justification": "Singer poses a rigorous moral argument: if you saw a child drowning in a pond, you would ruin your shoes to save them. He argues that global poverty offers us the same choice every day. A challenging ethical call to action that defines the moral obligations of the wealthy.",
                "tags": ["Ethics", "Philosophy", "Poverty", "Activism"]
            },
            {
                "query": "Winners Take All Anand Giridharadas",
                "justification": "A scathing critique of 'MarketWorld' philanthropy. Giridharadas argues that elites use 'giving back' as a way to avoid losing power. By offering band-aids instead of systemic reform, they maintain the very inequality they claim to fight. A necessary check on modern techno-philanthropy.",
                "tags": ["Sociology", "Politics", "Philanthropy", "Inequality"]
            },
            {
                "query": "Blueprint for Revolution Srdja Popovic",
                "justification": "Popovic, a leader of the movement that toppled Milosevic, offers a handbook for non-violent resistance. He treats revolution as a design problem, showing how humor, branding, and low-risk actions can mobilize the public and undermine authoritarian pillars of support.",
                "tags": ["Activism", "Politics", "Strategy", "History"]
            }
        ]
    },
    {
        "title": "Avoiding Climate Catastrophe",
        "description": "Beyond the doom-scrolling. The technical, political, and economic paths to a livable future.",
        "books": [
            {
                "query": "The Ministry for the Future Kim Stanley Robinson",
                "justification": "Technically fiction, but heavily researched. It serves as the most comprehensive simulation we have of the next 30 years. It explores the carbon quantitative easing, geoengineering, and political violence that might actually be required to navigate the crisis. A blueprint disguised as a novel.",
                "tags": ["Science Fiction", "Climate Change", "Economics", "Futurism"]
            },
            {
                "query": "Sustainable Energy - Without the Hot Air David MacKay",
                "justification": "The physicist's guide to the energy transition. MacKay ruthlessly does the math on renewables vs. consumption, stripping away the marketing hype. 'If everyone does a little, we'll achieve only a little.' It provides the hard numbers needed to have a serious conversation about energy.",
                "tags": ["Energy", "Physics", "Sustainability", "Environment"]
            },
            {
                "query": "Drawdown Paul Hawken",
                "justification": "The most comprehensive plan ever proposed to reverse global warming. It ranks the 100 most substantive solutions (like refrigerant management and educating girls) by potential impact and cost. It shifts the narrative from 'mitigation' (slowing down) to 'drawdown' (reversing).",
                "tags": ["Environment", "Technology", "Policy", "Reference"]
            },
            {
                "query": "This Changes Everything Naomi Klein",
                "justification": "Klein argues that the climate crisis is not a technical problem but a result of the conflict between capitalism's need for endless growth and the planet's physical limits. She posits that saving the climate requires a fundamental restructuring of the global economic order.",
                "tags": ["Politics", "Economics", "Environment", "Capitalism"]
            },
            {
                "query": "Under a White Sky Elizabeth Kolbert",
                "justification": "Kolbert explores the 'control of nature.' We have messed up the planet so badly that the only solution might be more intervention (geoengineering, gene drives). It is a report from the cutting edge of the Anthropocene, asking if we can solve problems created by our own ingenuity.",
                "tags": ["Science", "Environment", "Technology", "Journalism"]
            }
        ]
    },
    {
        "title": "Effective Self-Learning",
        "description": "Metacognition and the art of mastering new skills without a syllabus.",
        "books": [
            {
                "query": "Ultralearning Scott Young",
                "justification": "Young deconstructs the strategies of aggressive self-learners (like the Polgar sisters or Feynman). He outlines principles like metalearning, directness, and retrieval practice. It is a tactical manual for anyone who needs to acquire hard skills rapidly outside of a university.",
                "tags": ["Education", "Productivity", "Psychology", "Self-Help"]
            },
            {
                "query": "Make It Stick Peter Brown",
                "justification": "Cognitive scientists demolish standard study habits (highlighting, re-reading). They show that learning requires 'desirable difficulties'—active recall, interleaving, and spacing. This is the evidence-based guide to how the brain actually encodes long-term memory.",
                "tags": ["Psychology", "Education", "Science", "Memory"]
            },
            {
                "query": "Mindstorms Seymour Papert",
                "justification": "Papert, the father of constructionism, argued that learning happens best when we build things. Computers shouldn't be used to program children; children should program computers. A visionary look at how technology can enable deep, exploratory learning rather than rote instruction.",
                "tags": ["Education", "Technology", "Computer Science", "Philosophy"]
            },
            {
                "query": "Peak Anders Ericsson",
                "justification": "Ericsson is the researcher behind the '10,000 hour rule.' He clarifies that practice alone isn't enough; it must be 'deliberate practice' with feedback and specific goals. He debunks the myth of innate talent, arguing that expert performance is largely a result of specific training methods.",
                "tags": ["Psychology", "Skill Acquisition", "Science"]
            },
            {
                "query": "A Mind for Numbers Barbara Oakley",
                "justification": "Though framed for math, this is a guide to learning *anything* difficult. Oakley explains the difference between 'focused' and 'diffuse' thinking modes and how to toggle between them to solve problems. A practical toolkit for overcoming procrastination and mental blocks.",
                "tags": ["Education", "Mathematics", "Productivity", "Neuroscience"]
            }
        ]
    },
    {
        "title": "Diplomacy and Negotiation",
        "description": "Navigating conflict, understanding leverage, and finding agreement in high-stakes environments.",
        "books": [
            {
                "query": "Never Split the Difference Chris Voss",
                "justification": "Voss, a former FBI hostage negotiator, rejects the academic 'win-win' approach. He teaches tactical empathy, labeling, and the use of 'No.' It is a field manual for high-pressure emotional negotiations where logic fails and psychology rules.",
                "tags": ["Business", "Psychology", "Communication", "Sales"]
            },
            {
                "query": "Diplomacy Henry Kissinger",
                "justification": "A magisterial history of international relations from the 17th century to the Cold War. Kissinger analyzes how the balance of power, legitimacy, and national interest have shaped the modern world order. Essential for understanding the grand strategy of states.",
                "tags": ["History", "Politics", "International Relations", "Strategy"]
            },
            {
                "query": "Getting to Yes Roger Fisher",
                "justification": "The classic text from the Harvard Negotiation Project. It introduced the concept of 'principled negotiation'—separating the people from the problem and focusing on interests rather than positions. It remains the standard framework for cooperative conflict resolution.",
                "tags": ["Business", "Law", "Communication", "Classic"]
            },
            {
                "query": "The Guns of August Barbara Tuchman",
                "justification": "Tuchman chronicles the failure of diplomacy that led to WWI. It is a study in miscomputation, rigid alliances, and the momentum of war plans. A terrifying lesson in how intelligent leaders can sleepwalk into a catastrophe that nobody wanted.",
                "tags": ["History", "War", "Politics", "Classic"]
            },
            {
                "query": "Schelling, The Strategy of Conflict Thomas Schelling",
                "justification": "Schelling applied game theory to the Cold War. He introduced concepts like the 'focal point' and valid threats. It explains how limiting one's own options (burning the ships) can be a source of bargaining power. A rigorous analysis of deterrence and credibility.",
                "tags": ["Game Theory", "Economics", "Strategy", "Cold War"]
            }
        ]
    }
]

def get_openlibrary_data(query):
    """
    Search OpenLibrary for the best match.
    Returns dict with edition_key, title, cover_id, ebook_access.
    """
    try:
        url = "https://openlibrary.org/search.json"
        params = {
            "q": query,
            "fields": "key,title,author_name,cover_i,first_publish_year,edition_key,ebook_access",
            "limit": 5 # Fetch more to find a borrowable one
        }
        resp = requests.get(url, params=params)
        data = resp.json()
        
        if not data.get("docs"):
            print(f"No results for: {query}")
            return None
        
        # Prioritize borrowable
        docs = data["docs"]
        def priority_score(doc):
            access = doc.get('ebook_access', 'no_ebook')
            if access in ['borrowable', 'public', 'printdisabled']:
                return 1
            return 0
        docs.sort(key=priority_score, reverse=True)
        
        doc = docs[0]
        
        # We need a valid edition key. 'edition_key' is a list.
        edition_keys = doc.get("edition_key", [])
        if not edition_keys:
            print(f"No edition key for: {query}")
            return None
            
        edition_key = edition_keys[0]
        
        return {
            "edition_key": edition_key,
            "title": doc.get("title"),
            "cover_id": doc.get("cover_i"),
            "ebook_access": doc.get("ebook_access")
        }
        
    except Exception as e:
        print(f"Error searching {query}: {e}")
        return None

def populate():
    if os.path.exists("thebestbookon_seed.db"):
        print("Seed file found. Restoring from 'thebestbookon_seed.db'...")
        shutil.copy("thebestbookon_seed.db", "thebestbookon.db")
        print("Database restored.")
        return

    print("Seed file not found. Starting fresh population from OpenLibrary...")
    from main import SessionLocal, Prompt, Submission, Vote, Tag, Favorite

    db = SessionLocal()
    
    print("Starting data population...")
    
    for prompt_data in DATA:
        print(f"Processing Prompt: {prompt_data['title']}")
        
        # 1. Create/Get Prompt
        prompt = db.query(Prompt).filter(Prompt.title == prompt_data['title']).first()
        if not prompt:
            prompt = Prompt(
                title=prompt_data['title'],
                description=prompt_data['description'],
                creator_username=USER_ORACLE
            )
            db.add(prompt)
            db.commit()
            db.refresh(prompt)
        
        # 2. Process Books
        for book_item in prompt_data['books']:
            print(f"  > Fetching: {book_item['query']}")
            
            # Rate limit slightly
            time.sleep(0.5) 
            
            ol_data = get_openlibrary_data(book_item['query'])
            
            if not ol_data:
                print("    Failed to find book data, skipping.")
                continue
            
            # Check for existing submission
            existing_sub = db.query(Submission).filter(
                Submission.prompt_id == prompt.id,
                Submission.title == ol_data['title'] # Loose check
            ).first()
            
            if existing_sub:
                print("    Already submitted.")
                continue
                
            # Create Submission
            submission = Submission(
                prompt_id=prompt.id,
                openlibrary_edition_key=ol_data['edition_key'],
                title=ol_data['title'],
                cover_id=ol_data['cover_id'],
                ebook_access=ol_data['ebook_access'],
                submitter_username=USER_ORACLE
            )
            db.add(submission)
            # Need to add to session to get ID? No, not yet.
            
            # Handle Tags
            for tag_name in book_item['tags']:
                tag_obj = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag_obj:
                    tag_obj = Tag(name=tag_name)
                    db.add(tag_obj)
                    db.commit() # Commit to get ID
                
                if tag_obj not in submission.tags:
                    submission.tags.append(tag_obj)
            
            db.commit()
            db.refresh(submission)
            
            # Create Vote (+1) with Comment
            vote = Vote(
                submission_id=submission.id,
                voter_username=USER_ORACLE,
                value=1,
                comment=book_item['justification']
            )
            db.add(vote)
            db.commit()
            print(f"    Submitted: {ol_data['title']}")
            
    db.close()
    print("Population complete.")

if __name__ == "__main__":
    populate()
