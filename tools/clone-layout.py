import sys
import re
import pcbnew

templateReferences = [
    "U201",
    "U202",
    "J201",
    "C201",
    "C202",
    "R201",
    "R202",
    "R203",
    "R204",
    "R205",
    "C203",
    "C204",
    "C205",
    "C206"
]

board = pcbnew.LoadBoard("fk-atlas.kicad_pcb")

numberOfClones = 5
originalRect = None
clonesX = 1
clonesY = 4
deltaX = pcbnew.FromMM(100)
deltaY = pcbnew.FromMM(16)
templateRefModulo = 100
templateRefStart = 0

def clone():
    for templateRef in templateReferences:							#For each module in the template schema
        templateModule = board.FindModuleByReference(templateRef)				#Find the corresponding module in the input board
        if templateModule is not None:
            cloneReferences = []
            templateReferenceNumber = (re.findall(r"\d+", templateRef)).pop(0)		#Extract reference number (as string)

            for i in range(0, numberOfClones-1):						#Create list of references to be cloned of this module in the template
                cloneRefNumber = int(templateReferenceNumber) + (i+1)*templateRefModulo	#Number of the next clone
                cloneReferences.append(re.sub(templateReferenceNumber, "", templateRef) + str(cloneRefNumber))	#String reference of the next clone
            print 'Original reference: ', templateRef, ', Generated clone references', cloneReferences

            for counter, cloneRef in enumerate(cloneReferences):				#Move each of the clones to appropriate location
                templatePosition = templateModule.GetPosition()
                cloneModule = board.FindModuleByReference(cloneRef)
                if cloneModule is not None:
                    if cloneModule.GetLayer() is not templateModule.GetLayer():			#If the cloned module is not on the same layer as the template
                        cloneModule.Flip(pcbnew.wxPoint(1, 1))						#Flip it around any point to change the layer
                    vect = pcbnew.wxPoint(templatePosition.x + (counter + 1) % clonesX * deltaX, templatePosition.y + (counter + 1) // clonesX * deltaY) #Calculate new position
                    cloneModule.SetPosition(vect)						#Set position
                    cloneModule.SetOrientation(templateModule.GetOrientation())			#And copy orientation from template
                else:
                    print 'Module to be moved (', cloneRef, ') is not found in the board.'
        else:
            print 'Module ', templateRef, ' was not found in the template board'

    for i in range(0, board.GetAreaCount()):
        zone = board.GetArea(i)
        if zone.GetLayer() == 41:
            originalRect = zone.GetBoundingBox()
            print("Area to clone", originalRect.GetOrigin(), originalRect.GetWidth(), originalRect.GetHeight())

    modules = board.GetModules()
    for i in range(0, board.GetAreaCount()):						#For all the zones in the template board
        zone = board.GetArea(i)
        if originalRect.Contains(zone.GetPosition()) and zone.GetLayer() is not 41:		#If the zone is inside the area to be cloned (the comment zone) and it is not the comment zone (layer 41)
            for i in range(1, numberOfClones):						#For each target clone areas
                zoneClone = zone.Duplicate()						#Make copy of the zone to be cloned
                zoneClone.Move(pcbnew.wxPoint(i % clonesX * deltaX, i // clonesX * deltaY))		#Move it inside the target clone area
                for module in modules:								#Iterate through all the pads (also the cloned ones) in the board...
                    for pad in module.Pads():
                        if zoneClone.HitTestInsideZone(pad.GetPosition()) and pad.IsOnLayer(zoneClone.GetLayer()):		#To find the (last) one inside the cloned zone. pad.GetZoneConnection() could also be used
                            zoneClone.SetNetCode(pad.GetNet().GetNet())			#And set the (maybe) correct net for the zone
                board.Add(zoneClone)

    tracks = board.GetTracks()
    cloneTracks = []
    for track in tracks:
        if track.HitTest(originalRect):							#Find tracks which touch the comment zone
            for i in range(1, numberOfClones):						#For each area to be cloned
                cloneTrack = track.Duplicate()						#Copy track
                cloneTrack.Move(pcbnew.wxPoint(i%clonesX*deltaX, i//clonesX*deltaY))		#Move it
                cloneTracks.append(cloneTrack)						#Add to temporary list
    for track in cloneTracks:								#Append the temporary list to board
        tracks.Append(track)

modules = board.GetModules()
for module in modules:
    module.Reference().SetVisible(False)

board.Save("fk-atlas-cloned.kicad_pcb")
