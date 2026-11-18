#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "FlashlightActor.generated.h"

class UStaticMeshComponent;
class USpotLightComponent;
class USceneComponent;

UCLASS()
class PILLARENCOUNTER_API AFlashlightActor : public AActor
{
    GENERATED_BODY()

public:
    AFlashlightActor();

    // Taschenlampe ein- und ausschalten
    UFUNCTION(BlueprintCallable, Category = "Flashlight")
    void ToggleLight();

    // Prüfen, ob das Licht eingeschaltet ist
    UFUNCTION(BlueprintPure, Category = "Flashlight")
    bool IsLightOn() const;

    // Taschenlampe aufheben
    // HoldPoint kann eine Desktop-Kamera oder VR-Hand sein
    UFUNCTION(BlueprintCallable, Category = "Flashlight")
    void PickUp(USceneComponent* HoldPoint);

    // Taschenlampe fallen lassen
    UFUNCTION(BlueprintCallable, Category = "Flashlight")
    void Drop();

    // Prüfen, ob die Taschenlampe gehalten wird
    UFUNCTION(BlueprintPure, Category = "Flashlight")
    bool IsHeld() const;

protected:

    // 3D-Modell der Taschenlampe
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Flashlight")
    TObjectPtr<UStaticMeshComponent> BodyMesh;

    // Lichtquelle der Taschenlampe
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Flashlight")
    TObjectPtr<USpotLightComponent> SpotLight;

private:

    // Speichert, ob die Taschenlampe gerade gehalten wird
    bool bIsHeld = false;
};