#include "FlashlightActor.h"

#include "Components/StaticMeshComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/SceneComponent.h"

AFlashlightActor::AFlashlightActor()
{
    PrimaryActorTick.bCanEverTick = false;

    // Gehäuse der Taschenlampe
    BodyMesh = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("BodyMesh")
    );

    SetRootComponent(BodyMesh);

    // Muss beweglich sein, damit wir die Taschenlampe
    // später an Kamera oder VR-Controller befestigen können
    BodyMesh->SetMobility(EComponentMobility::Movable);

    // Lichtstrahl
    SpotLight = CreateDefaultSubobject<USpotLightComponent>(
        TEXT("SpotLight")
    );

    SpotLight->SetupAttachment(BodyMesh);
    SpotLight->SetMobility(EComponentMobility::Movable);

    // Licht tritt entlang der positiven X-Achse aus
    SpotLight->SetRelativeLocation(FVector(20.f, 0.f, 0.f));

    // Lichteinstellungen
    SpotLight->SetIntensity(5000.f);
    SpotLight->SetAttenuationRadius(1500.f);
    SpotLight->SetInnerConeAngle(15.f);
    SpotLight->SetOuterConeAngle(25.f);

    // Anfangs ausgeschaltet
    SpotLight->SetVisibility(false);
}


// ==========================================
// LICHT EIN- UND AUSSCHALTEN
// ==========================================

void AFlashlightActor::ToggleLight()
{
    if (!SpotLight)
    {
        return;
    }

    SpotLight->SetVisibility(!SpotLight->IsVisible());
}


// ==========================================
// LICHTSTATUS ABFRAGEN
// ==========================================

bool AFlashlightActor::IsLightOn() const
{
    return SpotLight && SpotLight->IsVisible();
}


// ==========================================
// TASCHENLAMPE AUFHEBEN
// ==========================================

void AFlashlightActor::PickUp(USceneComponent* HoldPoint)
{
    // Sicherheitsprüfungen
    if (!HoldPoint || bIsHeld || !BodyMesh)
    {
        return;
    }

    // Bisherigen Physik- und Kollisionszustand merken
    const bool bWasSimulatingPhysics =
        BodyMesh->IsSimulatingPhysics();

    const ECollisionEnabled::Type PreviousCollision =
        BodyMesh->GetCollisionEnabled();

    // Physik deaktivieren
    BodyMesh->SetSimulatePhysics(false);

    // Kollision deaktivieren, damit die Taschenlampe
    // nicht mit dem Spieler kollidiert
    BodyMesh->SetCollisionEnabled(
        ECollisionEnabled::NoCollision
    );

    // Taschenlampe am Haltepunkt befestigen
    const bool bAttached = AttachToComponent(
        HoldPoint,
        FAttachmentTransformRules::SnapToTargetNotIncludingScale
    );

    if (!bAttached)
    {
        // Falls das Befestigen fehlschlägt:
        // vorherigen Zustand wiederherstellen
        BodyMesh->SetCollisionEnabled(PreviousCollision);
        BodyMesh->SetSimulatePhysics(bWasSimulatingPhysics);
        return;
    }

    // Taschenlampe wird jetzt gehalten
    bIsHeld = true;
}


// ==========================================
// TASCHENLAMPE FALLEN LASSEN
// ==========================================

void AFlashlightActor::Drop()
{
    if (!bIsHeld || !BodyMesh)
    {
        return;
    }

    // Taschenlampe von Kamera oder VR-Hand lösen
    DetachFromActor(
        FDetachmentTransformRules::KeepWorldTransform
    );

    // Kollision wieder aktivieren
    BodyMesh->SetCollisionEnabled(
        ECollisionEnabled::QueryAndPhysics
    );

    // Schwerkraft / Physik aktivieren
    BodyMesh->SetSimulatePhysics(true);

    // Taschenlampe wird nicht mehr gehalten
    bIsHeld = false;
}


// ==========================================
// PRÜFEN, OB TASCHENLAMPE GEHALTEN WIRD
// ==========================================

bool AFlashlightActor::IsHeld() const
{
    return bIsHeld;
}